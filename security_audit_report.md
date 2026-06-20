# AutoShip-CLI 安全审计报告

**审计范围**：`src/autoship/core/sandbox.py`、`src/autoship/adapters/upload/docker.py`、`src/autoship/cli/commands/plugin.py`、`src/autoship/core/audit_logger.py`、`src/autoship/core/registry_client.py`、`src/autoship/adapters/tool_adapter.py`、`src/autoship/plugins/docker_ship.py`、`src/autoship/plugins/security_scan.py`、`src/autoship/core/llm_client.py`、`src/autoship/adapters/providers/*.py`、`src/autoship/cli/commands/*.py`、`src/autoship/models/config.py` 及关联模块。

**审计方法**：静态代码审查，重点关注命令注入、权限逃逸、供应链完整性、敏感信息泄露和不可信代码执行。

**总体结论**：项目存在多处可导致远程代码执行或沙箱逃逸的高危/严重问题，建议优先修复 `verify`/`fix` 命令注入、LLM 补丁自动应用、插件安装供应链校验以及沙箱降级执行问题。

---

## 严重（Critical）

### C1. `verify` 命令接受任意用户输入并直接 `subprocess.run` 执行
- **文件/行号**：`src/autoship/cli/commands/verify.py:38-88`
- **影响**：攻击者可通过 `autoship verify "$(rm -rf /)"` 等参数直接执行任意系统命令。
- **修复建议**：不再直接执行用户输入字符串；改为从配置或白名单中选择预定义验证命令，或在 `subprocess.run` 前对命令进行严格校验。

### C2. `fix` 命令将 LLM 返回的补丁直接 `git apply` / `patch` 应用到代码库
- **文件/行号**：`src/autoship/cli/commands/fix.py:30-70`、`src/autoship/cli/commands/fix.py:120-170`
- **影响**：LLM 输出可被提示词注入或模型本身误导，导致任意文件写入/覆盖、恶意代码注入或 RCE；`--apply` / `--yes` 可跳过确认。
- **修复建议**：对补丁进行语法校验、限制可修改文件路径白名单、禁止 `--apply` 自动应用、要求人工 review；可考虑在隔离环境中先应用补丁并运行测试。

### C3. 插件安装将用户/注册表提供的包规格直接传给 `pip`/`uv`
- **文件/行号**：`src/autoship/cli/commands/plugin.py:205-282`、`src/autoship/cli/commands/plugin.py:505-551`
- **影响**：恶意注册表项或用户输入可指定恶意 PyPI/URL/VCS 包，导致安装并执行任意代码；`--skip-trust-check` 可绕过信任提示。
- **修复建议**：只允许来自注册表的包名，严格校验 `source_for_pip` 格式（包名 + 可选版本）；对 `untrusted/community` 插件强制沙箱并校验签名/哈希；移除 `--skip-trust-check` 选项或需要额外高权限确认。

### C4. 沙箱网络隔离默认不强制，失败后回退到无隔离执行
- **文件/行号**：`src/autoship/core/sandbox.py:70-82`、`src/autoship/core/sandbox.py:117-139`、`src/autoship/core/sandbox.py:160-176`
- **影响**：当 `required=False`（默认）且无 `unshare`/`firejail` 时，不可信插件在普通子进程中运行且保留网络访问；即使配置隔离，工具失败时也会自动回退到无隔离执行。
- **修复建议**：将 `SandboxConfig.required` 默认改为 `True`；回退到无隔离前必须显式失败或征得用户同意；安装 `community/untrusted` 插件时若无可用隔离工具应拒绝执行。

---

## 高危（High）

### H1. 注册表索引远程拉取无签名/完整性校验，且可回退到本地缓存
- **文件/行号**：`src/autoship/core/registry_client.py:71-117`
- **影响**：中间人或篡改缓存可导致分发恶意插件索引；`_fetch_remote` 仅校验 HTTP 状态码，不校验 JSON 签名或哈希。
- **修复建议**：为注册表索引添加签名或哈希校验（例如 minisign/ECDSA）；首次下载或 `--force` 同步时提示用户确认索引指纹。

### H2. 插件注册表记录的 `sha256`/`signature` 从未被验证
- **文件/行号**：`src/autoship/cli/commands/plugin.py:284-298`、`src/autoship/cli/commands/plugin.py:505-551`、`src/autoship/core/plugin_registry.py:53-66`
- **影响**：即使注册表提供哈希和签名，安装/更新流程仅存储不验证，无法防止包被替换或篡改。
- **修复建议**：在安装/更新前，对下载的 wheel/sdist 计算 sha256 并与注册表值比对；若提供签名则使用项目公钥验证。

### H3. 审计日志脱敏策略不完整，可能泄露密钥
- **文件/行号**：`src/autoship/core/audit_logger.py:184-198`
- **影响**：仅对键名包含子串的字段脱敏（如 `mytoken` 不会被匹配），且不会识别值中的敏感内容（如 stdout/stderr 中可能包含密钥、token）。
- **修复建议**：使用精确键名匹配 + 正则匹配值中的高熵字符串/密钥模式；对无法识别的 payload 字段默认脱敏处理。

### H4. `commit` 命令使用 `shlex.split` 解析 `EDITOR` 环境变量后执行
- **文件/行号**：`src/autoship/cli/commands/commit.py:88-99`
- **影响**：恶意 `EDITOR` 值（如 `vim; curl ... | sh`）可导致命令注入，但 `shlex.split` 可降低风险；仍需警惕复杂 payloads。
- **修复建议**：对 `EDITOR` 使用 `shlex.split` 后，仅执行第一个元素并校验其是否在已知编辑器白名单内，拒绝包含 shell 元字符或路径遍历的值。

### H5. `verify` 失败日志明文写入用户主目录，可能包含密钥
- **文件/行号**：`src/autoship/cli/commands/verify.py:19-27`
- **影响**：`~/.local/state/autoship/last_error.txt` 默认权限可能较宽松，若验证命令输出包含 secrets 则会造成持久化泄露。
- **修复建议**：在写入前对 stdout/stderr 进行与审计日志相同的密钥脱敏处理；设置文件权限 `0o600`。

---

## 中危（Medium）

### M1. 审计日志、注册表缓存、插件注册表文件未显式设置安全权限
- **文件/行号**：`src/autoship/core/audit_logger.py:73-78`、`src/autoship/core/registry_client.py:62-69`、`src/autoship/core/plugin_registry.py:125-132`
- **影响**：默认 umask 下文件可能被同系统其他用户读取，导致审计记录、缓存索引或插件元数据泄露。
- **修复建议**：创建目录/文件后调用 `chmod(path, 0o700)` / `chmod(file, 0o600)`，确保仅所有者可读写。

### M2. `fix` 命令自动读取错误日志中的文件路径并发送给 LLM
- **文件/行号**：`src/autoship/cli/commands/fix.py:82-102`
- **影响**：错误输出中的任意文件路径会被读取并加入 LLM prompt，可能泄露项目外敏感文件（如 `~/.ssh/id_rsa` 被错误日志引用时）。
- **修复建议**：限制读取路径必须在 `project_root` 内且属于允许扩展名白名单；对文件大小和读取范围做限制；提示用户正在读取哪些文件。

### M3. `clean` / `upload` 等命令依赖外部工具但由配置或用户输入决定行为
- **文件/行号**：`src/autoship/adapters/tool_adapter.py:54-62`、`src/autoship/adapters/upload/docker.py:40-47`、`src/autoship/adapters/upload/pypi.py:39-48`、`src/autoship/adapters/upload/github.py:39-46`
- **影响**：虽然当前实现使用列表参数而非 shell 字符串执行，降低了注入风险，但外部工具链的劫持（PATH 污染）仍可导致执行恶意二进制。
- **修复建议**：对关键外部工具校验绝对路径或 SHA256 哈希；考虑使用虚拟环境隔离的已知工具版本。

### M4. `docker_ship` 插件从配置读取 `build_args` 并直接传入 `docker build`
- **文件/行号**：`src/autoship/plugins/docker_ship.py:42-44`
- **影响**：虽然 `subprocess.run` 使用列表参数，但 `--build-arg` 值来自配置，若配置文件被篡改可能注入意外构建参数（如 `foo=$(...)` 在 Dockerfile 中仍会被 shell 解析）。
- **修复建议**：对 `build_args` 键值做白名单校验；对值中的 shell 元字符进行转义或拒绝。

### M5. 配置加载允许环境变量覆盖任意字段，可能无意中启用高危功能
- **文件/行号**：`src/autoship/core/config_center.py:74-108`、`src/autoship/core/config_center.py:133-193`
- **影响**：`AUTOSHIP_DOCKER_SHIP__ENABLED=1` 等可覆盖配置；恶意环境变量可启用上传、SIEM 转发或更改注册表 URL。
- **修复建议**：对通过环境变量可覆盖的字段做白名单；敏感字段（如 `siem_url`、`siem_token`、`base_url`）禁止通过环境变量设置或需额外确认。

---

## 低危（Low）

### L1. 审计日志 SIEM 转发失败仅记录 debug，无告警
- **文件/行号**：`src/autoship/core/audit_logger.py:200-211`
- **影响**：SIEM 长时间不可达时本地仍静默，企业场景下可能导致审计事件丢失而未被发现。
- **修复建议**：增加失败计数并在 CLI 退出时输出告警；支持配置最大连续失败次数后回退到本地队列。

### L2. `TelemetryCollector` 端点来自环境变量且未校验 URL 格式
- **文件/行号**：`src/autoship/core/telemetry.py:54-142`
- **影响**：恶意环境变量可将遥测数据发送到攻击者服务器，但遥测内容仅包含命令名、退出码等元数据，影响有限。
- **修复建议**：校验 `endpoint` 为 HTTPS URL，并默认仅允许已知域名或要求用户显式启用。

### L3. 模型网关错误信息可能泄露后端 URL 或模型名称
- **文件/行号**：`src/autoship/adapters/providers/openai_compatible.py:92-103`、`src/autoship/adapters/providers/azure_openai.py:82-91` 等
- **影响**：异常消息中包含模型服务商返回的状态码，虽不敏感，但verbose 模式下可能暴露更多后端细节。
- **修复建议**：统一错误消息格式，避免在日志中打印 `base_url` 或 API 密钥；对verbose 输出也做脱敏。

---

## 优先级修复路线图

1. **立即修复（P0）**：`verify` 命令注入、`fix` 自动应用补丁、插件安装供应链校验、沙箱默认降级执行。
2. **短期内修复（P1）**：注册表索引完整性校验、插件签名/哈希验证、审计日志脱敏增强、`EDITOR` 校验、失败日志脱敏与权限。
3. **中期改进（P2）**：文件权限收紧、环境变量覆盖白名单、`build_args` 校验、SIEM/Telemetry 端点校验。

---

*报告生成日期：2026-06-19*
