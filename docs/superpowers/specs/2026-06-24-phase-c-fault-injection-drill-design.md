# Phase C — 故障注入式演练设计

## 目标
人为制造 6-8 个真实“麻烦”，验证 AutoShip-CLI 能否给出清晰错误、合理降级、有效排查信息，并在修复后恢复正常。

## 故障场景

| 编号 | 故障 | 注入方式 | 预期行为 |
|------|------|---------|---------|
| 1 | 配置文件损坏 | 写入非法 TOML 到 `.autoship.toml` | `autoship doctor` 或任意命令提示配置错误 |
| 2 | 验证命令不在白名单 | `autoship verify ls` | 返回 `VerifyError: command_disallowed` |
| 3 | 验证命令不存在 | `autoship verify nonexistent-tool` | 返回 `VerifyError: command_not_found` |
| 4 | 插件注册表损坏 | 写入非法 JSON 到 `~/.config/autoship/registry.json` | `plugin list` 优雅降级，不崩溃 |
| 5 | 磁盘缓存不可写 | 将缓存目录设为只读 | `doctor` 报 cache warning/error |
| 6 | 敏感环境变量覆盖被阻止 | 设置 `AUTOSHIP_LLM__API_KEY` | `config list` 不暴露 key，日志记录 blocked |
| 7 | 清理工具缺失 | 配置 `clean.tools = ["zzblack"]` | `doctor` 报 clean_missing，`clean` 跳过/失败优雅 |
| 8 | 模型后端不可达 | 配置指向不存在端口的 `model.backends` | `doctor` 报 model_unreachable；`commit` 降级为默认消息 |

## 执行方式
- 每个故障在独立临时目录注入，使用 CLI 触发相关命令。
- 记录实际 exit code、关键输出片段、是否给出建议。
- 对可自动修复的故障（如恢复配置文件、清理环境变量）执行恢复步骤并重新验证。

## 通过标准
- 所有故障均被正确识别，CLI 不因异常而崩溃。
- 错误信息包含可操作建议（如 `Run autoship init`、`Install the required tool`）。
- 敏感值在任何输出与审计日志中均被脱敏。
