# Phase A — 端到端场景测试设计

## 目标
模拟 4 位不同背景的开发者，在真实复杂项目中使用 AutoShip-CLI 完成“初始化 → 诊断 → 清理 → 验证 → 修复 → 提交 → 上传预览”的完整工作流，确认 CLI 在多样化项目结构、语言环境和业务场景下可用且输出符合预期。

## 角色与项目

| 角色 | 项目 | 复杂度 | 核心验证点 |
|------|------|--------|-----------|
| 初级全栈开发者 | FastAPI + 简单前端 monorepo | 多目录、有未格式化代码、测试失败 | init、clean、verify pytest、fix、commit、upload dry-run |
| DevOps 工程师 | Python CLI + Docker 交付项目 | Dockerfile、entrypoint、CI 配置 | init、doctor、verify python --version、upload docker dry-run、plugin search/info |
| 开源插件作者 | 使用 autoship-sdk 开发新插件 | 完整的 plugin 包、hook、测试 | autoship-sdk 模板、本地 plugin install、plugin list/trust、verify pytest |
| 安全敏感型企业开发者 | 含敏感环境变量/误提交密钥的仓库 | 审计、脱敏、安全扫描 | config list 脱敏、audit export、verify ruff、敏感键 redaction |

## 执行方式
- 在临时目录中生成每个项目的完整文件树。
- 通过 `python -m autoship` 调用 CLI，使用 `--yes`/`--dry-run` 保证非交互。
- 捕获 exit code、stdout/stderr，与预期结果比对。
- 汇总为 Markdown + JSON 报告。

## 通过标准
- 4 个场景全部完成且关键步骤（init、clean、doctor/verify、commit、upload dry-run、audit/config）符合预期。
- 不存在未处理的异常崩溃。
- 敏感信息在 config/audit 输出中被脱敏。
