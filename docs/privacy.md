# 隐私政策（Privacy Policy）

AutoShip 坚持**本地优先**与**默认关闭**原则：除非你显式开启，否则不会收集、上传或共享任何使用数据。

## 1. 我们收集哪些数据

### 1.1 遥测数据（默认关闭）

当用户在配置中启用 `[telemetry].enabled = true` 后，AutoShip 会在每条命令结束时上传匿名使用统计，字段包括：

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

所有遥测记录在写入本地日志或远程发送前都会经过 PII 过滤器，路径、密钥、邮箱等敏感值会被替换为 `<path>` 或 `<redacted>`。

更详细的遥测配置、批量发送与端点安全规则请参见 [docs/telemetry.md](telemetry.md)。

### 1.2 审计日志（本地默认开启）

AutoShip 默认在本地写入结构化审计日志，用于安全排查与合规审计。审计日志包含：

- 命令调用事件与退出状态
- 配置变更与插件操作
- 模型调用请求（已脱敏）
- SIEM 转发记录（若启用）

审计日志同样会经过脱敏处理，敏感键值与常见 token 模式会被替换为 `***`。

## 2. 数据存储位置

| 数据类型 | 默认路径 | 权限 |
|---|---|---|
| 遥测本地日志 | `~/.autoship/telemetry.logl` | 所有者可读写 |
| 审计日志 | `~/.autoship/logs/audit.{YYYY-MM-DD}.jsonl` | 目录 `0o700`，文件 `0o600` |
| 配置与缓存 | `~/.autoship/` 或项目根目录 | 遵循最小权限原则 |

## 3. 数据保留与清理

### 3.1 遥测本地日志

遥测本地日志为 JSON Lines 格式，**不会自动轮转或清理**。用户可随时手动删除：

```bash
rm ~/.autoship/telemetry.logl
```

### 3.2 审计日志

审计日志默认保留 **30 天**，可通过配置调整：

```toml
[audit]
retention_days = 30
```

运行以下命令清理过期日志：

```bash
autoship audit cleanup
```

清理逻辑会删除 `mtime` 早于 `retention_days` 天的 `audit.*.jsonl` 文件。

## 4. 如何开启或关闭遥测

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

在 `.autoship.toml` 中：

```toml
[telemetry]
enabled = true
endpoint = "https://telemetry.autoship.dev/v1/events"
batch_size = 10
timeout = 5.0
allow_untrusted_endpoint = false
```

旧版 `telemetry_enabled = false` 仍然兼容，启动时会自动迁移到 `[telemetry].enabled`。

## 5. 远程端点安全

- 仅接受 `https://` 端点。
- 默认只允许向 `telemetry.autoship.dev` 发送。
- 若需要发送到其他域名，需同时满足：
  - 配置文件中设置 `allow_untrusted_endpoint = true`；
  - 或设置环境变量 `AUTOSHIP_TELEMETRY_ALLOW_UNTRUSTED=1`。
- 请求超时默认为 5 秒，最大不超过 30 秒。

## 6. 你的权利

- **知情权**：所有收集字段均在本文档与 [docs/telemetry.md](telemetry.md) 公开说明。
- **控制权**：遥测默认关闭，用户拥有完全控制权，可随时开启或关闭。
- **审查权**：本地遥测与审计日志均以明文 JSON Lines 存储，用户可直接查看。
- **删除权**：手动删除本地日志文件即可清除所有已收集的本地数据。

## 7. 联系我们

如有隐私相关问题，请通过以下方式联系：

- GitHub Issues：[https://github.com/MS33834/autoship-cli/issues](https://github.com/MS33834/autoship-cli/issues)
- 邮件：team@autoship.dev
