---
title: 为什么选 AutoShip
---
# 为什么选 AutoShip

> 在选择交付自动化工具前，先看清 AutoShip 与主流方案（husky / pre-commit / GitHub Actions / commitizen）的差异。本页诚实地标注 AutoShip 不占优的维度，帮你判断是否适合你的项目。

## 与主流工具对比

| 维度 | AutoShip | husky | pre-commit | GitHub Actions | commitizen |
|---|---|---|---|---|---|
| 本地优先（默认不联网） | ✅ 是 | ✅ 是 | ⚠️ 需联网下载 hook | ❌ 运行在云端 | ✅ 是 |
| AI 生成 commit message | ✅ 内置（本地/云模型可选） | ❌ 无 | ❌ 无 | ❌ 无 | ⚠️ 仅按模板生成，非 AI |
| 内置安全扫描（提交前） | ✅ 是 | ❌ 无（需配 hook） | ⚠️ 依赖第三方 hook | ⚠️ 需自建 | ❌ 无 |
| 插件化扩展 | ✅ pluggy Hook | ⚠️ 仅 git hook 脚本 | ✅ hook 仓库 | ✅ Marketplace | ⚠️ 有限 |
| 多语言 i18n 文档 | ✅ 中/英/日 | ❌ 仅英文 | ❌ 仅英文 | ❌ 仅英文 | ⚠️ 部分翻译 |
| 配置复杂度 | 低（`autoship init --yes` 一键） | 低 | 中（需写 `.pre-commit-config.yaml`） | 高（YAML 工作流） | 中 |
| 是否需联网 | 否（核心命令可离线） | 否 | 是（首次拉 hook） | 是 | 否 |
| 触发时机 | 本地手动 / 任意阶段 | git hook | git hook | push / PR | 手动 |
| 覆盖范围 | clean + verify + commit + upload | 仅 git hook | 仅检查 | 任意（但需联网） | 仅 commit 规范 |

## AutoShip 占优的场景

- **想要一条命令跑完「清理 → 验证 → 提交 → 上传」**：AutoShip 把四步串成统一流程，无需自行拼装 hook 与 CI。
- **关心代码隐私、默认不想把代码送云**：本地优先 + 可选本地 AI 模型，核心命令离线可用。
- **希望 commit message 由 AI 根据真实 diff 生成**：而非仅套模板。
- **中文/日文团队**：原生 i18n 文档与 CLI 提示，降低上手门槛。

## AutoShip 不占优的维度（诚实说明）

- **生态规模**：husky / pre-commit 拥有庞大的社区与现成 hook 仓库，AutoShip 的插件生态尚在起步，可用第三方插件较少。
- **运行环境**：AutoShip 依赖 Python ≥ 3.10；husky / commitizen 对 Node 生态更友好，纯前端项目可能更顺手。
- **CI 集成成熟度**：GitHub Actions 拥有海量官方/社区 Action 与稳定托管，AutoShip 的 CI 集成仍在完善。
- **历史项目兼容**：已有成熟 `.pre-commit-config.yaml` 的项目迁移到 AutoShip 需重写部分 hook，短期有迁移成本。
- **Windows 稳定性**：核心功能支持 Windows，但部分路径 edge case 仍存在，详见 [已知问题](known-issues.md)。

## 何时选择其他工具

- 只需要 git hook 触发已有脚本 → **husky** 更轻量。
- 只需要代码格式/lint 检查，且依赖庞大 hook 仓库 → **pre-commit** 更合适。
- 需要在 PR 上跑复杂 CI 矩阵（多 OS、多矩阵） → **GitHub Actions**。
- 只想强制 Conventional Commits 规范、不需要 AI → **commitizen** 足够。

AutoShip 与上述工具并非互斥：你可以在 CI 用 GitHub Actions、本地用 AutoShip，或用 AutoShip 调用 pre-commit 的检查器。

## 下一步

- [快速开始](quickstart.md)
- [命令参考](commands/index.md)
- [插件开发](plugin-development.md)
