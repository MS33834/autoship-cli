---
title: 已知问题
---
# 已知问题

> 本页诚实记录 AutoShip 当前已知的限制与未解决问题，便于你评估是否影响使用。下文问题若标记「计划修复」，将在后续版本处理。

## `verify --fix` 无 AI 后端不可用

`verify --fix` 依赖 AI 模型生成修复建议。若未配置任何模型后端（既无本地 Ollama，也无云端 provider），该子命令会直接报错退出，**不会**自动回退到模板修复。

- 临时方案：使用 `autoship verify pytest`（不带 `--fix`）只做验证；
- 或参考 [快速开始](quickstart.md) 的「+5 分钟带 AI 版」配置 Ollama。
- 状态：设计如此，非 bug。

## Windows 路径 edge case

在 Windows 上存在若干已知路径问题：

- 含空格或非 ASCII 字符的用户目录（如 `C:\Users\张三\`）可能导致审计日志路径解析异常；
- `upload --target docker` 在 PowerShell 7 以下版本对 `\\wsl$\` 路径支持不全；
- `.autoship.toml` 中反斜杠路径需转义或改用正斜杠。

状态：计划在 1.1 版本统一路径处理。

## 大仓库 `clean` 性能

在文件数超过约 5 万的大型仓库中，`clean` 的全量扫描可能耗时较长（数十秒级），且内存占用偏高。

- 临时方案：在 `.autoship.toml` 中配置 `clean.exclude` 跳过 `node_modules`、`venv`、构建产物等目录；
- 或使用 `clean --paths src/` 限定扫描范围。
- 状态：增量扫描与并行化在路线图中。

## 三语翻译可能滞后

中文为源语言，英文与日文为翻译版本。新功能或修订可能先在中文文档落地，en/ja 存在数小时到数天的滞后窗口。

- 影响：新版本发布后的短时间内，en/ja 文档可能未同步最新命令或选项。
- 状态：CI 已加入 i18n 完整性检查，缺译会告警；mike 版本化文档启用后会更严格。

## mike 版本化文档待 1.0 后启用

`mkdocs.yml` 已声明 `version.provider: mike`，但版本切换器尚未正式启用。当前所有访问者看到的是最新构建，无法切换历史版本。

- 状态：待 1.0 正式发布后启用 mike 子域名与版本选择器；
- 期间如需查阅历史文档，请直接到 GitHub 对应 tag 下查看 `docs/` 目录。

## 反馈与跟踪

如遇上述问题之外的新故障，请：

- 查看 [故障排查](troubleshooting.md)；
- 在 [GitHub Issues](https://github.com/MS33834/autoship-cli/issues) 搜索或提交 issue，并附上 `autoship doctor` 输出与 `--verbose` 日志。
