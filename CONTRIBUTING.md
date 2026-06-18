# 贡献指南

感谢你对 AutoShip-CLI 的关注！我们欢迎并鼓励社区贡献。

## 行为准则

参与本项目即表示你同意遵守我们的[行为准则](CODE_OF_CONDUCT.md)。

## 如何贡献

- 报告 bug：请使用 GitHub Issues，并附上复现步骤、环境信息与最小复现示例。
- 提出建议：通过 GitHub Discussions 分享你的想法。
- 提交代码：Fork 仓库，创建特性分支，提交 Pull Request。

## 开发环境

本项目使用 [uv](https://docs.astral.sh/uv/) 管理依赖。

```bash
uv sync --all-extras --dev
uv run pytest
```

## 代码规范

- 使用 [ruff](https://docs.astral.sh/ruff/) 进行格式化和 lint。
- 使用 [pyright](https://microsoft.github.io/pyright/) 进行严格类型检查。
- 提交信息使用英文，遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。
- 新增功能必须包含测试，保持覆盖率不低于 85%。

## 提交 Pull Request

1. 确保所有检查通过：`uv run ruff check src tests`、`uv run pyright`、`uv run pytest`。
2. 运行安全扫描：`uv run bandit -r src -ll`。
3. 在 PR 描述中说明改动原因、影响范围与测试方式。
4. 等待维护者 review，必要时进行修改。

## 许可证

通过贡献代码，你同意所贡献的内容采用与项目一致的 [MIT](LICENSE) 许可证。
