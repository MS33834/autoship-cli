# 遥测与隐私（Telemetry & Privacy）

AutoShip 默认**关闭遥测**。只有当你显式启用后，才会收集并发送匿名的使用统计信息。

## 收集哪些数据

启用遥测后，每条命令结束时会上传以下字段：

| 字段 | 示例 | 说明 |
|---|---|---|
| `command` | `"clean"` | 命令名称 |
| `exit_code` | `0` | 退出码 |
| `duration_ms` | `123.45` | 命令执行耗时（毫秒） |
| `exception_type` | `"ConfigError"` | 异常类型（如有） |
| `exception_lineno` | `42` | 异常发生行号（如有） |
| `python_version` | `"3.12.4"` | Python 主版本 |
| `platform` | `"Linux"` | 操作系统家族 |
| `metrics_summary` | `{...}` | 全局计数器摘要 |

**不会收集任何以下内容：**

- 文件内容、diff、源码
- 文件路径、工作目录、主机名
- 命令参数、环境变量
- API key、token、密码、邮箱等凭证
- 用户名或其他个人身份信息（PII）

所有写入本地日志或远程发送的记录都会先经过 PII 过滤器，路径、密钥、邮箱等敏感值会被替换为 `<path>` 或 `<redacted>`。

## 如何开启或关闭

### 命令行

```bash
# 开启遥测
autoship config telemetry --enable

# 关闭遥测
autoship config telemetry --disable

# 查看当前状态
autoship config telemetry --status
```

### 配置文件

在 `.autoship.toml` 中添加：

```toml
[telemetry]
enabled = true
endpoint = "https://telemetry.autoship.dev/v1/events"
batch_size = 10
timeout = 5.0
allow_untrusted_endpoint = false
```

旧版配置中的 `telemetry_enabled = false` 仍然兼容，启动时会自动迁移到 `[telemetry].enabled`。

## 远程端点安全规则

- 仅接受 `https://` 端点。
- 默认只允许向 `telemetry.autoship.dev` 发送。
- 若需要发送到其他域名，需同时满足：
  - 配置文件中设置 `allow_untrusted_endpoint = true`；
  - 或设置环境变量 `AUTOSHIP_TELEMETRY_ALLOW_UNTRUSTED=1`。
- 请求超时默认为 5 秒，最大不超过 30 秒。

## 批量发送与本地日志

遥测事件先写入本地 `~/.autoship/telemetry.logl`，并在内存中缓冲。当缓冲数量达到 `batch_size`（默认 10）或 CLI 退出前调用 `flush()` 时，会一次性批量发送到配置的端点。发送失败不会影响 CLI 的正常使用。

## 隐私政策摘要

1. 默认关闭，用户拥有完全控制权。
2. 数据匿名化，不包含任何 PII。
3. 所有出站遥测均通过 HTTPS，且受域名校验保护。
4. 本地日志与远程数据均经过脱敏处理。
5. 用户可随时通过 `autoship config telemetry --disable` 退出。

如需审计本地遥测内容，可查看 `~/.autoship/telemetry.logl`（JSON Lines 格式）。
