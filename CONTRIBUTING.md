## 仓库说明

**本仓库以 GitHub 为主仓，GitCode 为镜像。**

- 主仓库地址：https://github.com/MS33834/autoship-cli
- GitCode 镜像：https://gitcode.com/badhope/autoship-cli

请直接在 **GitHub 主仓** 提交 Issue 和 Pull Request。GitCode 仅用于代码镜像，不处理 Issue/PR。

---

# 贡献指南

感谢你对 AutoShip-CLI 的关注！我们欢迎并鼓励社区贡献。

## 行为准则

参与本项目即表示你同意遵守我们的[行为准则](https://github.com/MS33834/autoship-cli/blob/main/CODE_OF_CONDUCT.md)。

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

## 远程仓库健康检查（每次提交前必做）

> **强制要求**：每次开始工作、每次提交前、每次推送后，都必须检查远程仓库状态。
> 这是项目纪律，避免遗漏 PR/Issue、CI 红了不知道、分支堆积无人处理。

检查清单（用 GitHub API 或网页）：

1. **Pull Request**：`https://github.com/MS33834/autoship-cli/pulls?state=open`
   - 有无待 review/合并的 PR（含 Dependabot 依赖升级 PR）？
   - PR 的 CI 检查是否全绿？有无冲突？
   - 长期未处理的 PR 是否需要决策（合并/关闭/催办）？

2. **Issue**：`https://github.com/MS33834/autoship-cli/issues?state=open`
   - 有无未回复的 Issue？
   - 有无标注了 bug 但未修复的？
   - 有无 Plugin Submission 类型的 Issue 待审核？

3. **分支**：`git fetch --all --prune && git branch -r`
   - 有无残留的特性分支需要清理？
   - GitCode 镜像的 main HEAD 是否与 GitHub 一致？（`git ls-remote origin main` 与 `git ls-remote gitcode main` 比对）

4. **CI 状态**：`https://github.com/MS33834/autoship-cli/actions`
   - main 分支最新 commit 的所有 workflow 是否全绿（CI / E2E / Nightly / Deploy Website / Release）？
   - 最近一次 Nightly 是否成功？失败的话看日志定位。
   - 有无卡住的 pending run？

5. **依赖安全**：
   - Dependabot 是否有新的安全告警？（Settings → Security advisories）
   - `uv run pip-audit --desc` 本地是否清洁？

**处理原则**：

- 发现红的 CI：先修复再继续新工作，不要在红的 CI 上叠加新提交。
- 发现 Dependabot PR：评估是否升级；跨大版本升级（如 setup-uv v3→v7）统一在一个分支处理并本地验证，不逐个合并。
- 发现 GitCode 镜像落后：立即 `git push gitcode main` 同步。
- 检查结果记录在当次 commit message 或 review 文档中，便于回溯。

一键检查脚本（可选，本地执行）：

```bash
# 快速查看 GitHub 仓库状态（需 GITHUB_TOKEN 环境变量）
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/MS33834/autoship-cli/pulls?state=open | jq 'length'
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/MS33834/autoship-cli/issues?state=open | jq '[.[] | select(.pull_request == null)] | length'
git fetch --all --prune && git branch -r
```

## 提交插件到 Registry

我们欢迎第三方插件！请按以下流程提交：

1. 使用 [`autoship-sdk`](https://pypi.org/project/autoship-sdk/) 创建插件项目并发布到 PyPI。
2. 在 GitHub 上选择 **Plugin Submission** 模板创建 issue。
3. 维护者会根据以下清单审核：
   - 插件遵循 AutoShip hook spec，不执行未授权操作。
   - 包含 README、开源许可证和基本测试。
   - 名称不与现有插件冲突，符合 `autoship-*` 命名约定。
   - 请求 `verified` 时需提供 SHA256 校验和或 GPG 签名。
4. 审核通过后，插件会被加入 `src/autoship/registry/plugins.json`，
   并自动出现在 [Plugin Registry Web UI](https://autoship-cli.github.io/autoship-registry/)。

## 许可证

通过贡献代码，你同意所贡献的内容采用与项目一致的 [MIT](https://github.com/MS33834/autoship-cli/blob/main/LICENSE) 许可证。
