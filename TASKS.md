# AutoShip-CLI 下一阶段任务清单

> 状态：P0 与 P1-1 / P1-2 / P1-3 已完成并合并至 `main`。  
> 本清单供团队承接剩余 **P1（短期内修复）** 与 **P2（中期改进）** 项使用。

---

## 如何阅读本清单

- **优先级**：P1 > P2，建议按编号顺序处理。
- **验收标准**：每项包含 "完成标准"，修复后需在本地通过 `uv run ruff check src tests`、`uv run pyright`、`uv run pytest`。
- **安全扫描**：修复完成后运行 `uv run bandit -r src -ll`。
- **测试要求**：新增/修改的漏洞修复必须附带对应单元测试或集成测试。
- **提交流程**：
  1. 从最新 `main` 切出特性分支：`git switch -c feat/P1-X-short-desc`。
  2. 将分支推送到 **GitHub 主仓**（GitCode 仅作为镜像，不接受 Issue/PR）。
  3. 在 GitHub 创建 Pull Request，按 `.github/PULL_REQUEST_TEMPLATE.md` 填写说明。
  4. 等待 CI 全部通过 + review 通过后再合并。
  5. 合并后 GitCode 镜像会自动同步，无需再向 `gitcode/main` 直接推送。

---

## 团队分工（建议）

| 小组 | 负责范围 | 当前任务 |
|------|----------|----------|
| **安全组** | 审计日志脱敏、SIEM、文件权限、密钥/token 防护 | P1-5、P2-1、P2-6 |
| **CLI 命令组** | 各子命令的输入校验与沙箱行为 | P1-4、P2-2、P2-4 |
| **基础设施组** | 配置中心、外部工具、Telemetry、环境变量 | P2-3、P2-5、P2-7 |
| **模型网关组** | 模型后端错误处理与信息脱敏 | P2-8 |

> 各组按任务编号顺序推进；完成一项后在本文件勾选并在 GitHub issue #5 回复进度。

---

## P1 — 短期内修复（高优先级）

### P1-1 注册表索引远程拉取签名/完整性校验 ✅

- **状态**：已完成（PR #4 已合并）。
- **问题**：`src/autoship/core/registry_client.py:71-117` 仅校验 HTTP 状态码，不校验 JSON 签名或哈希；中间人或篡改缓存可导致分发恶意插件索引。
- **影响**：高危（H1）。
- **修复建议**：
  1. 为注册表索引添加签名或哈希校验（例如 minisign / ECDSA）。
  2. 首次下载或 `--force` 同步时提示用户确认索引指纹。
  3. 缓存回退逻辑必须在校验失败时拒绝使用旧缓存。
- **完成标准**：
  - `registry_client._fetch_remote` 在写入缓存前验证签名/哈希。
  - 校验失败时抛出可识别的 `RegistryError`，且不使用该索引。
  - 新增测试覆盖：合法签名通过、篡改签名失败、缓存被篡改失败。
- **相关文件**：`src/autoship/core/registry_client.py`、`src/autoship/exceptions.py`、注册表发布流程。

### P1-2 插件安装/更新时验证 sha256 与 signature ✅

- **状态**：已完成（PR #6 已合并）。
- **问题**：`src/autoship/cli/commands/plugin.py:284-298` 与 `505-551` 仅存储注册表提供的 `sha256`/`signature`，从不验证。
- **影响**：高危（H2）。
- **修复建议**：
  1. 在安装/更新前，对下载的 wheel/sdist 计算 sha256 并与注册表值比对。
  2. 若提供签名，则使用项目公钥验证（minisign / ECDSA / PGP 任选一种）。
  3. 验证失败时拒绝安装并记录审计日志。
- **完成标准**：
  - `_run_pip_install` 或 `_installed_version` 流程中插入校验步骤。
  - 缺失 sha256 的 `verified` 插件视为未验证并给出警告。
  - 新增测试：哈希匹配通过、哈希不匹配拒绝、签名验证通过/失败。
- **相关文件**：`src/autoship/cli/commands/plugin.py`、`src/autoship/core/plugin_registry.py`。

### P1-3 审计日志脱敏策略增强 ✅

- **状态**：已完成（PR #9 已合并）。
- **问题**：`src/autoship/core/audit_logger.py:184-198` 仅按键名子串脱敏，无法识别 `mytoken` 等键名，也不识别值中的密钥、token。
- **影响**：高危（H3）。
- **修复建议**：
  1. 精确键名匹配（如 `api_key`, `token`, `password`, `secret`）。
  2. 使用正则匹配值中的高熵字符串/密钥模式（如 `ghp_[A-Za-z0-9_]{36}`、`sk-[A-Za-z0-9]{48}` 等）。
  3. 对无法识别的 payload 字段默认脱敏处理（可选开关）。
- **完成标准**：
  - `audit_logger` 的脱敏函数覆盖键名、值模式、未知字段三种情况。
  - 单元测试覆盖：常见 token 格式被替换、非敏感字段保留、嵌套字典生效。
- **相关文件**：`src/autoship/core/audit_logger.py`、`tests/test_audit_logger.py`。

### P1-4 `commit` 命令 EDITOR 校验

- **问题**：`src/autoship/cli/commands/commit.py:88-99` 使用 `shlex.split` 解析 `EDITOR` 环境变量后执行，复杂 payload 仍可注入。
- **影响**：高危（H4）。
- **修复建议**：
  1. `shlex.split` 后仅执行第一个元素。
  2. 校验该元素是否在已知编辑器白名单内（`vim`, `nvim`, `emacs`, `nano`, `code`, `subl` 等）。
  3. 拒绝包含 shell 元字符或路径遍历的值。
- **完成标准**：
  - 白名单可配置；未知编辑器默认拒绝并提示。
  - 新增测试：合法编辑器通过、带分号的命令被拒绝、路径遍历被拒绝。
- **相关文件**：`src/autoship/cli/commands/commit.py`、`src/autoship/models/config.py`。

### P1-5 `verify` 失败日志脱敏与权限收紧

- **问题**：`src/autoship/cli/commands/verify.py:19-27` 将明文 stdout/stderr 写入 `~/.local/state/autoship/last_error.txt`，可能泄露密钥。
- **影响**：高危（H5）。
- **修复建议**：
  1. 写入前使用与审计日志相同的脱敏逻辑处理 stdout/stderr。
  2. 创建文件/目录时设置权限 `0o600`（文件）/`0o700`（目录）。
  3. 读取时若文件权限过宽给出警告。
- **完成标准**：
  - `_write_error_log` 调用脱敏函数并设置权限。
  - 新增测试：含 token 的 stderr 被脱敏、文件权限正确。
- **相关文件**：`src/autoship/cli/commands/verify.py`。

---

## P2 — 中期改进（中优先级）

### P2-1 审计日志、注册表缓存、插件注册表文件权限收紧

- **问题**：`src/autoship/core/audit_logger.py:73-78`、`src/autoship/core/registry_client.py:62-69`、`src/autoship/core/plugin_registry.py:125-132` 创建的文件默认 umask 可能被其他用户读取。
- **影响**：中危（M1）。
- **修复建议**：创建目录/文件后显式调用 `chmod(path, 0o700)` / `chmod(file, 0o600)`。
- **完成标准**：上述三个模块创建本地持久化文件时均设置仅所有者可读写。
- **相关文件**：`src/autoship/core/audit_logger.py`、`src/autoship/core/registry_client.py`、`src/autoship/core/plugin_registry.py`。

### P2-2 `fix` 命令读取文件路径限制

- **问题**：`src/autoship/cli/commands/fix.py:82-102` 读取错误日志中任意文件路径并发送给 LLM，可能泄露项目外文件（如 `~/.ssh/id_rsa`）。
- **影响**：中危（M2）。
- **修复建议**：
  1. 限制读取路径必须在 `project_root` 内。
  2. 属于允许扩展名白名单（`.py`, `.toml`, `.cfg`, `.ini`, `.yaml`, `.yml`, `.json` 等）。
  3. 限制文件大小；提示用户正在读取哪些文件。
- **完成标准**：`_collect_relevant_files` 加入路径与扩展名校验。
- **相关文件**：`src/autoship/cli/commands/fix.py`。

### P2-3 外部工具 PATH 污染防护

- **问题**：`src/autoship/adapters/tool_adapter.py:54-62`、`src/autoship/adapters/upload/docker.py:40-47` 等依赖外部工具，PATH 污染可导致执行恶意二进制。
- **影响**：中危（M3）。
- **修复建议**：
  1. 对关键外部工具校验绝对路径或 SHA256 哈希。
  2. 考虑使用虚拟环境隔离的已知工具版本。
- **完成标准**：至少对 `git`, `docker`, `twine`, `gh`, `patch` 提供可选的绝对路径/哈希校验配置。
- **相关文件**：`src/autoship/adapters/tool_adapter.py`、`src/autoship/adapters/upload/*.py`。

### P2-4 `docker_ship` 插件 `build_args` 校验

- **问题**：`src/autoship/plugins/docker_ship.py:42-44` 将配置读取的 `build_args` 直接传入 `docker build`，`foo=$(...)` 在 Dockerfile 中仍可能被 shell 解析。
- **影响**：中危（M4）。
- **修复建议**：
  1. 对 `build_args` 键名做白名单校验。
  2. 对值中的 shell 元字符进行转义或拒绝。
- **完成标准**：危险字符/键名被拒绝或转义，并记录警告。
- **相关文件**：`src/autoship/plugins/docker_ship.py`。

### P2-5 环境变量覆盖配置白名单

- **问题**：`src/autoship/core/config_center.py:74-108`、`133-193` 允许 `AUTOSHIP_DOCKER_SHIP__ENABLED=1` 等任意覆盖。
- **影响**：中危（M5）。
- **修复建议**：
  1. 对通过环境变量可覆盖的字段做白名单。
  2. 敏感字段（`siem_url`, `siem_token`, `base_url`, `api_key`）禁止通过环境变量设置或需额外确认。
- **完成标准**：ConfigCenter 加载环境变量时按白名单过滤，敏感字段被阻止。
- **相关文件**：`src/autoship/core/config_center.py`。

### P2-6 SIEM 转发失败告警

- **问题**：`src/autoship/core/audit_logger.py:200-211` SIEM 转发失败仅记录 debug，无告警。
- **影响**：低危（L1）。
- **修复建议**：增加失败计数并在 CLI 退出时输出告警；支持配置最大连续失败次数后回退到本地队列。
- **完成标准**：SIEM 连续失败 N 次后输出告警并停用转发。
- **相关文件**：`src/autoship/core/audit_logger.py`。

### P2-7 Telemetry 端点校验

- **问题**：`src/autoship/core/telemetry.py:54-142` 端点来自环境变量且未校验 URL 格式。
- **影响**：低危（L2）。
- **修复建议**：校验 `endpoint` 为 HTTPS URL，默认仅允许已知域名或要求用户显式启用。
- **完成标准**：非法/非 HTTPS 端点被拒绝并记录警告。
- **相关文件**：`src/autoship/core/telemetry.py`。

### P2-8 模型网关错误信息脱敏

- **问题**：`src/autoship/adapters/providers/openai_compatible.py:92-103`、`azure_openai.py:82-91` 等错误消息可能泄露后端 URL 或模型名称。
- **影响**：低危（L3）。
- **修复建议**：统一错误消息格式，避免打印 `base_url` 或 API 密钥；verbose 输出也做脱敏。
- **完成标准**：所有 provider 异常消息不再包含 URL/key；相关测试通过。
- **相关文件**：`src/autoship/adapters/providers/*.py`。

---

## 团队交接备注

- 已合并的 P0 / P1 修复见最近 8 个 commit：
  1. `feat(security): verify registry index signature and sha256 (P1-1)`
  2. `feat(security): verify plugin packages before install/update (P1-2)`
  3. `fix(ci): add missing npm install step in website workflow`
  4. `fix(sandbox): require isolation tooling by default`
  5. `fix(verify): validate command against allowlist and reject shell metacharacters`
  6. `fix(fix): remove --apply flag and validate patch paths before applying`
  7. `fix(i18n): guard against formatting exceptions`
  8. `fix(metrics): make Counter increments thread-safe and harden plugin stats loading`
- 本地质量门禁：`uv run ruff check src tests`、`uv run pyright`、`uv run pytest`。
- 安全扫描：`uv run bandit -r src -ll`。
- 未跟踪的 `*_report.md` 为审计/性能/质量报告，团队决定是否纳入版本控制。
- 提交修复请走 **GitHub Pull Request**，不要在 GitCode 发起 PR。
