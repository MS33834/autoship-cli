# AutoShip-CLI 下一阶段任务清单

> 状态：P0 与 P1-1 / P1-2 / P1-3 / P1-4 / P1-5 以及 P2-1 / P2-2 / P2-4 / P2-6 / P2-8 已完成并合并至 `main`。  
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
| **安全组** | 审计日志脱敏、SIEM、文件权限、密钥/token 防护 | 已完成 |
| **CLI 命令组** | 各子命令的输入校验与沙箱行为 | 已完成 |
| **基础设施组** | 配置中心、外部工具、Telemetry、环境变量 | 已完成 |
| **模型网关组** | 模型后端错误处理与信息脱敏 | 已完成 |

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

### P1-4 `commit` 命令 EDITOR 校验 ✅

- **状态**：已完成（PR #11 已合并）。
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

### P1-5 `verify` 失败日志脱敏与权限收紧 ✅

- **状态**：已完成（PR #12 已合并）。
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

### P2-1 审计日志、注册表缓存、插件注册表文件权限收紧 ✅

- **状态**：已完成（PR #17 已合并）。
- **问题**：`src/autoship/core/audit_logger.py:73-78`、`src/autoship/core/registry_client.py:62-69`、`src/autoship/core/plugin_registry.py:125-132` 创建的文件默认 umask 可能被其他用户读取。
- **影响**：中危（M1）。
- **修复建议**：创建目录/文件后显式调用 `chmod(path, 0o700)` / `chmod(file, 0o600)`。
- **完成标准**：上述三个模块创建本地持久化文件时均设置仅所有者可读写。
- **相关文件**：`src/autoship/core/audit_logger.py`、`src/autoship/core/registry_client.py`、`src/autoship/core/plugin_registry.py`。

### P2-2 `fix` 命令读取文件路径限制 ✅

- **状态**：已完成（本 PR）。
- **问题**：`src/autoship/cli/commands/fix.py:82-102` 读取错误日志中任意文件路径并发送给 LLM，可能泄露项目外文件（如 `~/.ssh/id_rsa`）。
- **影响**：中危（M2）。
- **修复建议**：
  1. 限制读取路径必须在 `project_root` 内。
  2. 属于允许扩展名白名单（`.py`, `.toml`, `.cfg`, `.ini`, `.yaml`, `.yml`, `.json` 等）。
  3. 限制文件大小；提示用户正在读取哪些文件。
- **完成标准**：`_collect_relevant_files` 加入路径与扩展名校验。
- **相关文件**：`src/autoship/cli/commands/fix.py`。

### P2-3 外部工具 PATH 污染防护 ✅

- **状态**：已完成（本 PR）。
- **问题**：`src/autoship/adapters/tool_adapter.py:54-62`、`src/autoship/adapters/upload/docker.py:40-47` 等依赖外部工具，PATH 污染可导致执行恶意二进制。
- **影响**：中危（M3）。
- **修复建议**：
  1. 对关键外部工具校验绝对路径或 SHA256 哈希。
  2. 考虑使用虚拟环境隔离的已知工具版本。
- **完成标准**：至少对 `git`, `docker`, `twine`, `gh`, `patch` 提供可选的绝对路径/哈希校验配置。
- **相关文件**：`src/autoship/adapters/tool_adapter.py`、`src/autoship/adapters/upload/*.py`。

### P2-4 `docker_ship` 插件 `build_args` 校验 ✅

- **状态**：已完成（本 PR）。
- **问题**：`src/autoship/plugins/docker_ship.py:42-44` 将配置读取的 `build_args` 直接传入 `docker build`，`foo=$(...)` 在 Dockerfile 中仍可能被 shell 解析。
- **影响**：中危（M4）。
- **修复建议**：
  1. 对 `build_args` 键名做白名单校验。
  2. 对值中的 shell 元字符进行转义或拒绝。
- **完成标准**：危险字符/键名被拒绝或转义，并记录警告。
- **相关文件**：`src/autoship/plugins/docker_ship.py`。

### P2-5 环境变量覆盖配置白名单 ✅

- **状态**：已完成（本 PR）。
- **问题**：`src/autoship/core/config_center.py:74-108`、`133-193` 允许 `AUTOSHIP_DOCKER_SHIP__ENABLED=1` 等任意覆盖。
- **影响**：中危（M5）。
- **修复建议**：
  1. 对通过环境变量可覆盖的字段做白名单。
  2. 敏感字段（`siem_url`, `siem_token`, `base_url`, `api_key`）禁止通过环境变量设置或需额外确认。
- **完成标准**：ConfigCenter 加载环境变量时按白名单过滤，敏感字段被阻止。
- **相关文件**：`src/autoship/core/config_center.py`。

### P2-6 SIEM 转发失败告警 ✅

- **状态**：已完成（PR #18 已合并）。
- **问题**：`src/autoship/core/audit_logger.py:200-211` SIEM 转发失败仅记录 debug，无告警。
- **影响**：低危（L1）。
- **修复建议**：增加失败计数并在 CLI 退出时输出告警；支持配置最大连续失败次数后回退到本地队列。
- **完成标准**：SIEM 连续失败 N 次后输出告警并停用转发。
- **相关文件**：`src/autoship/core/audit_logger.py`。

### P2-7 Telemetry 端点校验 ✅

- **状态**：已完成（本 PR）。
- **问题**：`src/autoship/core/telemetry.py:54-142` 端点来自环境变量且未校验 URL 格式。
- **影响**：低危（L2）。
- **修复建议**：校验 `endpoint` 为 HTTPS URL，默认仅允许已知域名或要求用户显式启用。
- **完成标准**：非法/非 HTTPS 端点被拒绝并记录警告。
- **相关文件**：`src/autoship/core/telemetry.py`。

### P2-8 模型网关错误信息脱敏 ✅

- **状态**：已完成（本 PR）。
- **问题**：`src/autoship/adapters/providers/openai_compatible.py:92-103`、`azure_openai.py:82-91` 等错误消息可能泄露后端 URL 或模型名称。
- **影响**：低危（L3）。
- **修复建议**：统一错误消息格式，避免打印 `base_url` 或 API 密钥；verbose 输出也做脱敏。
- **完成标准**：所有 provider 异常消息不再包含 URL/key；相关测试通过。
- **相关文件**：`src/autoship/adapters/providers/*.py`。

---

## P3 — 产品化冲刺（让 CLI 可用于真实项目）

P3 目标是把已完成的 MVP 功能在真实后端、真实仓库、真实 CI 环境中跑通，并补齐文档与分发能力，使 AutoShip 成为“可安装、可配置、可发布”的工具。

### 团队分工（P3）

| 小组 | 负责范围 | P3 任务 |
|------|----------|---------|
| **AI/模型组** | 本地模型后端、LLM prompt、fallback、token/cost | P3-1 |
| **发布/集成组** | PyPI/Docker 上传、包分发、版本发布 | P3-2、P3-3、P3-5 |
| **文档/UX组** | 命令参考、快速上手、错误提示、多语言 | P3-4、P3-6 |
| **安全/合规组** | 隐私、遥测、审计、权限 | P3-7 |
| **生态/插件组** | 插件注册表、发布流程、示例插件 | P3-8 |

### P3-1 AI 路径真实后端联测

- **Owner**：AI/模型组
- **问题**：当前 commit/verify --fix 仅在单元测试里 mock 了 ModelRouter，未在 Ollama、LM Studio、OpenAI 等真实后端下验证生成质量、错误处理与脱敏。
- **验收标准**：
  - 在 `tests/integration/ai_backends/` 下新增测试，使用环境变量或 fixtures 配置后端。
  - 至少验证 Ollama（本地）与 OpenAI-compatible（如 LM Studio）两种后端。
  - 验证失败（后端不可用、模型不存在、超时）时 CLI 给出清晰提示且不泄露 URL/key。
  - prompt 输出不包含原始 API key 或完整本地路径。
- **相关文件**：`src/autoship/adapters/providers/*.py`、`src/autoship/core/model_router.py`、`src/autoship/cli/commands/commit.py`、`src/autoship/cli/commands/verify.py`。
- **依赖**：P2-8 模型网关脱敏已完成。
- **状态**：✅ 已完成。新增 Ollama 与 LM Studio 集成测试，修复 OllamaGateway 使用标准 `/v1` OpenAI-compatible 端点，完成多角色 review 与修复，review 记录见 `docs/reviews/p3-1-ai-backend-integration.md`。

### P3-2 真实上传集成（PyPI / Docker）

- **Owner**：发布/集成组
- **问题**：upload 目前仅验证 `--dry-run`，真实 PyPI/Docker 路径未在集成环境中跑通。
- **验收标准**：
  - `autoship upload --target pypi` 能调用 `twine upload`（或等价工具）完成真实上传，并在测试环境使用 TestPyPI。
  - `autoship upload --target docker` 能完成 `docker build` + `docker push`。
  - 提供 `--repository-url` / `--dry-run` 明确区分测试与生产。
  - CI 中使用 mock 或临时 registry（如 `localstack`、本地 Docker registry）跑通上传路径。
- **相关文件**：`src/autoship/adapters/upload/*.py`、`src/autoship/cli/commands/upload.py`。
- **依赖**：P2-3 外部工具 PATH 校验已完成。
- **状态**：✅ 已完成。PyPI/Docker 适配器支持 `--repository-url` 与 `--registry`，默认使用 TestPyPI，新增本地 registry 集成测试，完成多角色 review 与修复，review 记录见 `docs/reviews/p3-2-upload-integration.md`。

### P3-3 安装包与分发验证

- **Owner**：发布/集成组
- **问题**：CLI 在源码环境下开发，未验证 `pip install autoship` 在干净环境是否可用。
- **验收标准**：
  - `python -m build` 生成 wheel/sdist 成功。
  - 在干净的虚拟环境中 `pip install dist/autoship-*.whl` 后，所有非 AI 命令可用。
  - entry point `autoship` 能正确找到并执行。
  - autoship-sdk 作为 extras 或 workspace 依赖关系清晰，无循环依赖。
- **相关文件**：`pyproject.toml`、`src/autoship/__main__.py`、`src/autoship/cli/main.py`。

### P3-4 完整命令参考文档

- **Owner**：文档/UX组
- **问题**：docs/commands.md 缺失或过时，用户无法查全命令参数。
- **验收标准**：
  - 每个子命令（init、clean、verify、fix、commit、upload、plugin、doctor、config、registry）都有独立的命令参考页。
  - 文档中的命令输出与实际 CLI 行为一致。
  - 提供中文与英文版本，并更新 `docs/demo.md` 中的链接。
- **相关文件**：`docs/commands/` 或 `docs/commands.md`、各 `src/autoship/cli/commands/*.py`。
- **依赖**：P3-6 错误提示稳定后文档再定稿。

### P3-5 GitHub Actions CI 流水线

- **Owner**：发布/集成组
- **问题**：已有 CI 配置但 dogfood/benchmarks 未接入自动化运行。
- **验收标准**：
  - CI 运行 `ruff`、`pyright`、`pytest`、`bandit`。
  - CI 运行 `python dogfood/dogfood.py` 并上传 `dogfood/report.json` artifact。
  - CI 运行 `python benchmarks/benchmark.py` 并保存/对比 `benchmarks/results.json`。
  - 发布 tag 时自动构建 wheel 并上传到 PyPI/TestPyPI。
- **相关文件**：`.github/workflows/ci.yml`、`.github/workflows/release.yml`。
- **依赖**：P3-3 打包验证完成。

### P3-6 错误消息与 UX 打磨

- **Owner**：文档/UX组
- **问题**：部分错误消息仍为英文或技术栈信息过重，多语言覆盖不完整。
- **验收标准**：
  - 所有用户可见错误消息都可通过 `zh.json` / `en.json` 翻译。
  - 常见错误（未初始化、未配置模型、未安装工具、上传失败）给出下一步操作建议。
  - `--help` 与各命令 help 文本经过统一润色。
  - 新增 UX 测试：验证 `--help` 输出无 Traceback、未知命令提示友好。
- **相关文件**：`src/autoship/cli/main.py`、各 `src/autoship/cli/commands/*.py`、`src/autoship/locales/*.json`。

### P3-7 遥测与隐私合规

- **Owner**：安全/合规组
- **问题**：Telemetry 已校验端点，但尚未提供用户可见的遥测说明与关闭方式文档。
- **验收标准**：
  - 在 `docs/privacy.md` 中说明收集哪些数据、存储多久、如何关闭。
  - CLI 首次启用遥测时提示用户（或默认关闭，需 opt-in）。
  - 提供 `autoship config telemetry --disable` 命令或等效配置项。
  - 审计日志保存策略（轮转、清理）写入文档与默认配置。
- **相关文件**：`src/autoship/core/telemetry.py`、`src/autoship/core/audit_logger.py`、`docs/privacy.md`。

### P3-8 插件商店与发布流程

- **Owner**：生态/插件组
- **问题**：registry-web 已可用，但缺少插件提交、审核、签名发布的 SOP。
- **验收标准**：
  - 在 `docs/plugin-publishing.md` 中定义插件元数据格式、签名/哈希要求、PR 模板。
  - `registry/plugins.json` 增加签名字段与审核状态字段，并更新 schema。
  - registry-web 能正确展示 verified / community 状态。
  - 提供至少 2 个经过审核的真实插件（docker-ship 可算一个，再新增一个）。
- **相关文件**：`registry/plugins.json`、`registry-web/*`、`docs/plugin-publishing.md`。

---

## P4 — 发布就绪（正式对外发布）

P4 目标是从“可用”走向“可信赖的产品”：稳定的发布节奏、完整的公开文档、可验证的安全性、活跃的插件生态。

### 团队分工（P4）

| 小组 | 负责范围 | P4 任务 |
|------|----------|---------|
| **发布/集成组** | 版本号、Changelog、自动化发布 | P4-1 |
| **文档/UX组** | 官方文档站、教程、视频/截图 | P4-2 |
| **生态/插件组** | 社区插件、审核、认证发布者 | P4-3 |
| **性能/测试组** | 大规模项目测试、回归、稳定性 | P4-4 |
| **安全/合规组** | 第三方安全审计、渗透测试 | P4-5 |
| **市场/运营组** | 发布通告、README、社交媒体 | P4-6 |

### P4-1 版本管理与发布流程

- **Owner**：发布/集成组
- **验收标准**：
  - 采用 SemVer，使用 `python-semantic-release` 或手动 tag + changelog。
  - 每次 release 自动生成 GitHub Release Notes 与 `CHANGELOG.md`。
  - 发布前 checklist 包含：测试通过、文档最新、签名密钥轮换、PyPI 上传成功。
- **相关文件**：`CHANGELOG.md`、`.github/workflows/release.yml`。

### P4-2 公开文档站点

- **Owner**：文档/UX组
- **验收标准**：
  - 使用 MkDocs / Docusaurus / 静态站点工具构建官方文档站。
  - 包含：快速开始、命令参考、插件开发、模型配置、隐私政策、FAQ。
  - CI 自动部署到 GitHub Pages 或自定义域名。
- **相关文件**：`docs/`、`mkdocs.yml` 或 `website/docs/`。

### P4-3 社区插件征集与审核

- **Owner**：生态/插件组
- **验收标准**：
  - 制定插件提交模板与审核 checklist。
  - 至少 5 个社区或官方插件进入 registry。
  - 明确 verified publisher 认证流程。
- **相关文件**：`docs/plugin-publishing.md`、`registry/plugins.json`。

### P4-4 性能与规模测试

- **Owner**：性能/测试组
- **验收标准**：
  - 在 1000+ 文件的项目上跑 `clean`、`verify`、`upload --dry-run` 并记录基线。
  - 多线程/并发场景下 metrics 与审计日志无竞争问题。
  - 长时间运行（如 CI 连续 24h）无内存泄漏。
- **相关文件**：`benchmarks/benchmark.py`、`dogfood/dogfood.py`、`src/autoship/core/metrics.py`。

### P4-5 安全审计与渗透测试

- **Owner**：安全/合规组
- **验收标准**：
  - 通过 `pip-audit`、`bandit`、 Dependabot/ Renovate 扫描。
  - 邀请第三方或内部红队做一轮针对 CLI 的渗透测试。
  - 所有 H/M 级别漏洞修复并发布安全公告。
- **相关文件**：`pyproject.toml`、CI 安全配置。

### P4-6 发布与市场推广

- **Owner**：市场/运营组
- **验收标准**：
  - README 包含安装、徽章、截图/asciinema、贡献指南。
  - 发布 blog/推特/掘金/知乎等渠道公告。
  - 收集首批用户反馈并形成下一轮迭代 issue。
- **相关文件**：`README.md`、`README.zh.md`、社交媒体文案。

---

## 团队交接备注

- 已合并的 P0 / P1 / P2 修复见最近 commit；P3/P4 为下一轮产品化计划。
- 本地质量门禁：`uv run ruff check src tests`、`uv run pyright`、`uv run pytest`。
- 安全扫描：`uv run bandit -r src -ll`。
- 新增 P3 任务建议从 `main` 切分支：`git switch -c feat/P3-X-short-desc`。
- 提交修复/功能请走 **GitHub Pull Request**，不要在 GitCode 发起 PR。
- 计划如有调整，请直接修改本文件并提交 PR。
