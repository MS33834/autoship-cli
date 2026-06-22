# 命令参考

AutoShip CLI 的所有命令遵循统一的生命周期：读取配置、调用 `pre_*` Hook、执行主体、调用 `post_*` Hook、记录审计日志。本文档提供每个命令的完整语法、参数、选项和示例。

## 全局选项

以下选项适用于所有命令，通常需要放在子命令之前（如 `autoship --verbose init`）：

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| `-v` | `--verbose` | `False` | 输出更详细的日志 |
| `-n` | `--dry-run` | `False` | 仅预览操作，不真正执行 |
| `-y` | `--yes` | `False` | 跳过交互式确认 |
| `-c` | `--config PATH` | - | 指定配置文件路径 |
| - | `--lang TEXT` | `auto` | 输出语言（`en`、`zh`、`auto`） |
| - | `--install-completion` | - | 为当前 shell 安装自动补全 |
| - | `--show-completion` | - | 显示当前 shell 的自动补全脚本 |

全局选项可通过 `autoship --help` 随时查看：

```bash
autoship --help
autoship --lang zh --help
```

## 命令列表

| 命令 | 说明 | 子命令 |
|---|---|---|
| [init](./init.md) | 为当前项目初始化 AutoShip 配置文件 | - |
| [clean](./clean.md) | 清理并格式化项目代码 | - |
| [verify](./verify.md) | 运行验证命令并捕获错误以供 AI 辅助修复 | - |
| [fix](./fix.md) | 请求 LLM 为最近一次验证失败生成修复建议 | - |
| [commit](./commit.md) | 生成提交信息并执行 Git 提交 | - |
| [upload](./upload.md) | 上传产物到已配置的目标 | - |
| [plugin](./plugin.md) | 管理插件 | `list`、`search`、`info`、`install`、`uninstall`、`rate`、`stats`、`trust`、`update` |
| [doctor](./doctor.md) | 诊断 AutoShip 环境与依赖 | - |
| [audit](./audit.md) | 导出或清理审计日志 | `export`、`cleanup` |
| [registry](./registry.md) | 查看插件注册表与同步索引 | `list`、`dashboard`、`sync` |
| [metrics](./metrics.md) | 查看运行时指标 | `show`、`export` |
| [config](./config.md) | 查看和管理 AutoShip 配置 | `list`、`get`、`telemetry` |

## 文档结构

- `index.md`（本页）：全局选项和命令索引。
- `<command>.md`：每个命令的独立参考页，包含概述、语法、参数、选项、示例、输出说明和相关命令。
- 复杂命令（`plugin`、`audit`、`registry`、`metrics`、`config`）的参考页包含子命令详细说明。

## 贡献方式

命令参考应保持与 CLI 实际 `--help` 输出一致。修改前请执行：

```bash
uv run python -m autoship <cmd> --help
```

如需新增命令，请同时更新本页命令列表表格和 `mkdocs.yml` 导航。
