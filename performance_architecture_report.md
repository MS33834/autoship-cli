# AutoShip CLI 性能与架构审计报告

**审计日期**：2026-06-19

**审计范围**：以下 11 个源文件

- `/workspace/autoship-cli/src/autoship/core/cache.py`
- `/workspace/autoship-cli/src/autoship/core/llm_client.py`
- `/workspace/autoship-cli/src/autoship/core/model_router.py`
- `/workspace/autoship-cli/src/autoship/core/plugin_registry.py`
- `/workspace/autoship-cli/src/autoship/adapters/model_gateway.py`
- `/workspace/autoship-cli/src/autoship/cli/main.py`
- `/workspace/autoship-cli/src/autoship/core/telemetry.py`
- `/workspace/autoship-cli/src/autoship/core/metrics.py`
- `/workspace/autoship-cli/src/autoship/core/registry_client.py`
- `/workspace/autoship-cli/src/autoship/core/context.py`
- `/workspace/autoship-cli/src/autoship/core/hook_dispatcher.py`

**审计方法**：逐行阅读源码，结合相关依赖（`src/autoship/adapters/providers/*.py`、`src/autoship/models/config.py`）分析调用链、I/O 模式、并发模型与资源生命周期。未对源码做任何修改。

---

## 整体结论

当前代码在“单次 CLI 命令”场景下功能完整，但在高并发、高频调用、长生命周期进程（如作为服务、Agent 循环、批量 fix/commit）等场景下存在明显的性能与架构瓶颈。主要问题集中在四类：

1. **异步代码路径中混入同步阻塞 I/O**（磁盘缓存、遥测发送、子进程）。
2. **短生命周期对象与连接池缺失**（每次请求新建 `httpx.AsyncClient`、每次调用重建 gateway）。
3. **锁粒度过粗或重复加锁**（`DiskCache` 全局锁、`MetricsRegistry` 单锁）。
4. **每次请求重复执行昂贵操作**（健康检查、临时脚本写入、全量注册表重写、大对象 JSON 序列化）。

建议优先处理高影响项，形成“持久客户端 + 异步 I/O + 缓存健康状态 + 进程/线程池复用”的架构。

---

## 高影响问题

### 1. LLM 异步客户端每请求新建 `AsyncClient`，无连接复用

- **影响**：高
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/llm_client.py:98-100`
- **描述**：`AsyncLlmClient.chat` 在每次调用时通过 `async with httpx.AsyncClient(...)` 创建并销毁客户端。每次请求都要重新解析 DNS、建立 TCP/TLS 连接、完成 TLS 握手，对于 OpenAI/OpenRouter 等远程 API 会显著增加延迟（几十到几百毫秒），且在高频调用场景下非常浪费。
- **优化建议**：
  - 在 `AsyncLlmClient.__init__` 中创建 `self._client = httpx.AsyncClient(headers=self._headers(), timeout=self.config.timeout)` 并复用。
  - 提供 `async def close(self)` 或实现 `__aenter__/__aexit__`，确保调用方（或 `LlmClient` 的同步包装）在生命周期结束时关闭连接池。
  - 若 `LlmClient` 仍作为同步入口，可在内部复用同一个 `AsyncClient` 实例并通过 `asyncio.run` 仅在必要时启动事件循环，而不是每次重建客户端。

### 2. 异步 LLM 路径中执行同步磁盘缓存 I/O，阻塞事件循环

- **影响**：高
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/llm_client.py:90-94`、`121-122`
  - `/workspace/autoship-cli/src/autoship/core/cache.py:75-94`、`96-106`
- **描述**：`AsyncLlmClient.chat` 在 `await` 之间直接调用 `self.cache.get()` 和 `self.cache.set()`，而 `DiskCache` 内部使用 `path.read_text()`、`json.dumps()`、`path.write_text()`、`tmp_path.replace()` 等同步文件系统调用。这些调用不会让出事件循环，会阻塞所有并发的异步任务。
- **优化建议**：
  - 将 `DiskCache` 提供异步接口（如 `async def aget/aset`），内部通过 `asyncio.to_thread()` 或 `aiofiles` 执行文件 I/O。
  - 在 `AsyncLlmClient` 中调用异步缓存接口，避免在 `async def chat` 中混入同步阻塞调用。
  - 考虑增加进程内 LRU 内存缓存层（如 `functools.lru_cache` 或 `cachetools.TTLCache`），减少对磁盘锁和文件 I/O 的依赖。

### 3. `DiskCache` 额外持有全局 `threading.Lock`，导致无关 key 串行化

- **影响**：高
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/cache.py:40`
  - `/workspace/autoship-cli/src/autoship/core/cache.py:79-80`
  - `/workspace/autoship-cli/src/autoship/core/cache.py:100-101`
  - `/workspace/autoship-cli/src/autoship/core/cache.py:111`
  - `/workspace/autoship-cli/src/autoship/core/cache.py:117`
- **描述**：`DiskCache` 除了每个 key 的文件锁（`fcntl.flock`）外，还在所有 `get/set/invalidate` 操作外加了一层 `self._lock`。文件锁已经足以保证跨进程/线程的 key 级安全，全局锁只会让不同 key 之间的并发请求强制串行，成为多线程/高并发场景下的瓶颈。
- **优化建议**：
  - 删除 `self._lock` 在 `get/set/invalidate` 中的使用，仅保留文件锁。
  - `clear()` 操作需要遍历目录，可保留一个本地锁或将其放到后台线程执行，避免与正常 key 操作竞争。

### 4. 遥测上报使用同步 HTTP POST，可能阻塞进程退出

- **影响**：高
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/telemetry.py:136-141`
  - `/workspace/autoship-cli/src/autoship/cli/main.py:92-93`
- **描述**：`TelemetryCollector._send` 使用同步 `httpx.post(..., timeout=5.0)`。`cli_entrypoint` 在 `finally` 块中调用 `telemetry.record()`，若用户启用遥测且网络抖动/服务端响应慢，CLI 退出会被阻塞最长 5 秒。
- **优化建议**：
  - 将远程发送改为后台线程 + 有界队列（如 `queue.Queue` + `threading.Thread`），在进程退出前使用 `atexit` 注册 flush，并设置更短的总超时（如 1–2 秒）。
  - 或者提供异步遥测收集器，在异步主循环中批量发送；CLI 场景下使用 `asyncio.wait_for` 限制退出等待时间。

### 5. `ModelRouter` 每次调用都重建 gateway 实例，丢失持久连接池

- **影响**：高
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/model_router.py:38-48`
  - `/workspace/autoship-cli/src/autoship/core/model_router.py:53`
  - `/workspace/autoship-cli/src/autoship/core/model_router.py:96`
- **描述**：`_gateways()` 在 `_chat()` 与 `select_backend()` 中每次都被调用，重新实例化所有 gateway（如 `OpenAIGateway`、`OllamaGateway`）。底层 gateway 在 `__init__` 中创建 `httpx.Client` 连接池，频繁重建导致 TCP 连接无法复用、DNS 反复解析，并增加 GC 压力。
- **优化建议**：
  - 在 `ModelRouter.__init__` 中根据 `config.model.backends` 一次性创建 `self._gateways` 列表并缓存。
  - 为 `ModelRouter` 实现 `close()` / 上下文管理器，统一关闭底层 `httpx.Client`。
  - 若配置支持热更新，可引入 TTL 或显式刷新机制，而不是每次请求重建。

### 6. `ModelRouter` 每次 chat 前同步执行健康检查，增加额外 RTT

- **影响**：高
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/model_router.py:61-64`
  - `/workspace/autoship-cli/src/autoship/core/model_router.py:99-104`
  - `/workspace/autoship-cli/src/autoship/core/model_router.py:110-114`
- **描述**：`_chat()` 在发送实际请求前先调用 `gateway.health()`（通常是一次 HTTP GET 到 `/models`），`select_backend()` 也重复该逻辑。这意味着每次模型调用至少多出 1 次、最坏 N 次（N 为 backend 数量）额外往返。对于本地 Ollama/LM Studio 等后端，少量请求时延迟不明显，但批量调用或后端偶发超时会被放大。
- **优化建议**：
  - 在 `ModelRouter` 中维护 `self._health_cache: dict[str, tuple[bool, float]]`，设置 TTL（如 5–15 秒），健康状态在 TTL 内复用。
  - 将“健康检查”与“请求失败回退”结合：直接发起 chat，仅在请求失败/超时时再尝试下一个 backend，减少正常路径上的额外 RTT。
  - 对 `select_backend()` 增加后台心跳任务，异步刷新状态。

### 7. 沙箱 hook 每次调用都向磁盘写入临时 Python 脚本

- **影响**：高
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/hook_dispatcher.py:201-215`
- **描述**：`_call_in_sandbox` 每次调用不可信插件时都会通过 `tempfile.NamedTemporaryFile` 把 `_SANDBOX_SCRIPT` 写入新的 `.py` 文件，调用结束后立即删除。脚本内容是常量，频繁的磁盘写入/删除在多插件、多 hook 调用场景下成为显著开销。
- **优化建议**：
  - 将 `_SANDBOX_SCRIPT` 一次性写入稳定路径（如 `~/.autoship/sandbox_runner_<version>.py`），按脚本内容哈希或版本号校验，避免每次重复写入。
  - 或使用 `sys.executable -c <script>` 直接通过命令行传脚本，彻底消除临时文件 I/O。
  - 注意：修改后仍需保证脚本来源可信，避免被恶意替换。

### 8. 每个 community/untrusted hook 都 fork 子进程，开销巨大

- **影响**：高
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/hook_dispatcher.py:205-215`
- **描述**：对于社区或未受信插件，每次 hook 调用都会创建新的子进程（`SandboxRunner.run`）。fork/exec + Python 解释器启动 + 模块重新导入的开销通常在百毫秒级；若一个命令触发多个 hook（如 `fix` 调用多个建议插件），总延迟会线性增长。
- **优化建议**：
  - 对沙箱 worker 使用进程池（`concurrent.futures.ProcessPoolExecutor`）或长生命周期子进程，复用解释器进程。
  - 在架构上区分“安全/可信”与“不可信”执行路径：可信插件继续在主进程通过 pluggy 调用，不可信插件批量发送到 worker 池执行。
  - 评估是否可将多个 hook 合并为一次 worker 调用，减少进程启动次数。

---

## 中影响问题

### 9. 同步 `LlmClient` 每次调用都 `asyncio.run`，无法复用事件循环

- **影响**：中
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/llm_client.py:159-165`
- **描述**：`LlmClient.chat` 和 `LlmClient.health` 每次调用都使用 `asyncio.run(...)`，会创建并关闭新的事件循环。虽然单次 CLI 命令影响有限，但在批量处理或嵌套调用场景下频繁创建事件循环既浪费资源，也阻止了并发批处理（无法将多个 prompt 合并到同一个事件循环并行发送）。
- **优化建议**：
  - 将 `AsyncLlmClient` 作为首选 API；`LlmClient` 作为薄同步包装，内部复用同一个事件循环或 `asyncio.run` 仅在顶层调用一次。
  - 提供批量接口 `async def batch_chat(self, prompts: list[tuple[str, str]]) -> list[str]`，充分利用连接池与并发。

### 10. LLM 缓存 key 未包含全部请求参数，存在命中率/正确性风险

- **影响**：中
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/llm_client.py:70-79`
- **描述**：`_cache_key` 仅包含 provider、model 和 messages。`max_tokens` 是当前唯一额外参数，但未来若加入 `temperature`、`top_p`、`presence_penalty` 等生成参数，或用户修改配置后，缓存 key 不会变化，可能返回错误的旧结果。即使当前，若 `LlmConfig.max_tokens` 改变，旧缓存仍会被命中。
- **优化建议**：
  - 将 `_payload(messages)` 中所有影响生成的字段（`max_tokens`、`temperature`、`top_p`、`stream` 等）都纳入缓存 key。
  - 例如：`json.dumps({"provider": ..., "model": ..., "payload": self._payload(messages)}, sort_keys=True)` 后再取 SHA256。

### 11. `RegistryClient` 使用临时 HTTP 客户端，无连接复用

- **影响**：中
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/registry_client.py:75`
- **描述**：`_fetch_remote` 使用顶层 `httpx.get(...)`，每次都会新建 `httpx.Client`、建立 TLS 连接。注册表刷新频率不高，但在网络较差或 CI 环境中多次触发时会累积延迟。
- **优化建议**：
  - 在 `RegistryClient.__init__` 中创建 `self._client = httpx.Client(timeout=10.0)` 并复用。
  - 实现 `close()` 方法，或在 `get_registry_client` 工厂中提供上下文管理器。

### 12. 注册表远程拉取同步阻塞 CLI 启动/命令执行

- **影响**：中
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/registry_client.py:75`
  - `/workspace/autoship-cli/src/autoship/core/registry_client.py:101-117`
- **描述**：`RegistryClient.get()` 在缓存未命中/过期时同步发起 `httpx.get(..., timeout=10.0)`。若远程 GitHub Raw 或注册表服务响应慢，整个 `plugin list/install` 等命令会被阻塞最长 10 秒，且无法取消。
- **优化建议**：
  - 将默认超时缩短为 3–5 秒，并启用 HTTP/2 或 keep-alive。
  - 在 CLI 启动路径中改为异步/后台刷新：先使用本地缓存或 bundled index 启动，后台线程异步更新缓存。
  - 提供 `--offline` / `--no-registry-update` 标志，避免不必要的网络等待。

### 13. `Histogram.percentile` 每次快照都对全量样本排序

- **影响**：中
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/metrics.py:76-85`
  - `/workspace/autoship-cli/src/autoship/core/metrics.py:87-96`
- **描述**：`percentile()` 在计算 p50/p95/p99 时对 `deque` 中的全部样本执行 `sorted()`，时间复杂度 O(N log N)。`to_dict()` 每次调用会触发 4 次排序。若 `snapshot()` 在每次遥测事件或高频 hook 后被调用，开销会显著增加。
- **优化建议**：
  - 使用 `sortedcontainers.SortedList` 维护有序样本，使 percentile 查询降至 O(log N) 或 O(1)。
  - 或者仅在查询/导出时计算 percentile，平时仅维护 `count/sum/min/max` 等聚合值；需要精确分位数时采用 TDigest、HdrHistogram 等近似算法。

### 14. `MetricsRegistry` 使用单把全局锁，所有指标操作串行

- **影响**：中
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/metrics.py:102-103`
  - `/workspace/autoship-cli/src/autoship/core/metrics.py:128-146`
- **描述**：所有 `inc/record/set/snapshot` 都竞争同一把 `threading.Lock`。在插件 hook 并发执行或 LLM 并发请求场景下，这把锁会成为热点，增加线程上下文切换。
- **优化建议**：
  - 对计数器使用 `threading.Lock` 细粒度锁（每个指标一把锁），或改用 `itertools.count`/原子整型包装。
  - `snapshot()` 可采用写时复制（copy-on-write）策略：加锁复制引用，释放锁后再序列化，减少锁持有时间。
  - 对于高频 Counter，可考虑 `collections.Counter` + `threading.local` 批量合并。

### 15. `PluginRegistry` 每次增删改都重写整个 `registry.json`

- **影响**：中
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/plugin_registry.py:86-106`
  - `/workspace/autoship-cli/src/autoship/core/plugin_registry.py:125-130`
- **描述**：`add/remove/trust` 每次都会调用 `_save()`，将内存中所有插件序列化后完整写入文件。批量安装多个插件时会产生多次全量写盘，既慢又增加损坏风险。
- **优化建议**：
  - 提供批量 API（如 `add_many`）并支持延迟保存/显式 `save()`。
  - 或者改为 append-only 日志 + 定期快照的存储模型，写操作变为 O(1) 追加。
  - 加文件锁或原子 rename，防止并发写导致 JSON 损坏。

### 16. `HookDispatcher` 每次沙箱调用都序列化完整 `AppConfig`

- **影响**：中
- **文件与行号**：
  - `/workspace/autoship-cli/src/autoship/core/hook_dispatcher.py:166-178`
  - `/workspace/autoship-cli/src/autoship/core/hook_dispatcher.py:188-191`
- **描述**：`_serialize_context` 每次都会调用 `context.config.model_dump(mode="json", warnings=False)`，把整个应用配置序列化为 JSON。配置对象通常较大且包含嵌套 Pydantic 模型，重复序列化带来不必要的 CPU 开销。
- **优化建议**：
  - 在 `CommandContext` 创建或首次使用时缓存序列化后的配置字典；沙箱调用直接复用。
  - 仅向沙箱传递插件真正需要的字段（如 `command`、`project_root`、`verbose`、`dry_run`、`yes`、`trace_id`），而不是整个 `AppConfig`。

### 17. 沙箱 payload 通过命令行参数传递，存在长度限制风险

- **影响**：中
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/hook_dispatcher.py:210`
- **描述**：`_call_in_sandbox` 将序列化后的 payload 作为 `sys.argv[1]` 传给子进程。当配置较大或 `extras` 包含较多数据时，可能超过操作系统对命令行参数长度的限制（Linux 典型约 2 MB，`ARG_MAX`），导致子进程启动失败。
- **优化建议**：
  - 将 payload 写入临时 JSON 文件，子进程通过文件路径读取；或写入 stdin。
  - 对敏感数据仍需注意临时文件权限与清理。

### 18. `TelemetryCollector` 每次事件都打开并关闭日志文件

- **影响**：中
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/telemetry.py:116-123`
- **描述**：`record_event` 每次调用都执行 `log_path.open("a", ...)`、`write()`、`close()`。虽然 Python 文件 I/O 有缓冲，但频繁的 open/close 系统调用仍高于批量写入。
- **优化建议**：
  - 使用后台线程 + 队列缓存事件，按条数/时间批量 flush；或复用文件句柄并在退出时关闭。
  - 若日志量小，至少使用 `open(..., buffering=...)` 并在 `TelemetryCollector` 生命周期内保持句柄打开。

### 19. `main_callback` 在每次命令回调中实例化 `AuditLogger` 并写入审计日志

- **影响**：中
- **文件与行号**：`/workspace/autoship-cli/src/autoship/cli/main.py:44-45`
- **描述**：每个命令都会创建 `AuditLogger(config)` 并立即 `record("cli.invoked", ...)`。如果 `AuditLogger` 内部涉及同步磁盘写入或网络转发，会直接阻塞 Typer 命令启动路径。当前未确认 `AuditLogger` 实现，但放在回调入口使其成为启动瓶颈的高风险点。
- **优化建议**：
  - 审查 `AuditLogger` 实现；若存在同步 I/O，改为后台队列 + 批量 flush。
  - 在 `main_callback` 中仅做轻量初始化，延迟首次写入或在必要时复用单例。

---

## 低影响问题

### 20. 缓存文件全部平铺在单一目录，未做分片

- **影响**：低
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/cache.py:47-49`
- **描述**：`_cache_path` 将 SHA256 哈希直接作为文件名存放到 `cache_dir` 根目录。当缓存条目成千上万时，大量文件集中在单个目录会降低文件系统查找/遍历性能，并影响 `clear()` 的 `glob` 速度。
- **优化建议**：
  - 按哈希前 2–4 字符分片到子目录，例如 `cache_dir / ha / sh / hash.cache`。
  - 保留向后兼容的迁移逻辑，或在 `clear()` 中按子目录分批删除。

### 21. `hook_dispatcher.call` 在 `fail_fast=False` 时遇到异常会提前返回空列表

- **影响**：低
- **文件与行号**：`/workspace/autoship-cli/src/autoship/core/hook_dispatcher.py:269-273`
- **描述**：当 `fail_fast=False` 时，理论上应继续执行剩余插件并收集所有成功结果；但当前实现捕获异常后直接 `return []`，不仅丢弃了已收集结果，也未继续迭代后续插件。这会降低插件生态的容错性和可组合性。
- **优化建议**：
  - 将 `return []` 改为继续循环：记录失败插件，保留已成功结果，循环结束后再返回 `results`。
  - 若需要区分部分失败场景，可返回包含结果与错误信息的结构体。

---

## 优先处理路线图

| 优先级 | 建议动作 | 预期收益 |
|---|---|---|
| P0 | 为 `AsyncLlmClient`、`ModelRouter`、`RegistryClient` 引入持久 HTTP 客户端 | 显著降低 TCP/TLS 握手延迟，减少 GC |
| P0 | 将 `DiskCache` 同步 I/O 移出异步路径，移除全局锁 | 避免事件循环阻塞与 key 级串行化 |
| P0 | 遥测/审计的同步网络/磁盘写入改为后台队列 | 消除 CLI 退出与启动阻塞 |
| P1 | `ModelRouter` 缓存健康状态并延迟重建 gateway | 减少每请求额外 RTT 与对象分配 |
| P1 | 沙箱 hook 复用脚本/进程池 | 降低多插件调用时的 fork/exec 开销 |
| P1 | 修复 `PluginRegistry` 全量写盘与 `Histogram` 排序开销 | 改善批量操作与高频指标性能 |
| P2 | 缓存 key 完整性、配置序列化缓存、命令行参数长度、目录分片等 | 提升正确性与可扩展性 |

---

## 备注

- 本次审计未运行测试或性能基准，也未修改任何源码。
- 部分问题（如遥测/审计阻塞）取决于未在本次审计范围内的 `AuditLogger`、`_OpenAIGatewayBase` 等实现细节，建议结合这些模块做进一步代码审查。
- 建议补充集成测试与压力测试，覆盖“多 backend fallback”“并发 hook”“高频 LLM 调用”等场景，以量化优化效果。
