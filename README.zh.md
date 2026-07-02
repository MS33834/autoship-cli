# AutoShip-CLI

<p align="right">
  <a href="README.md">English</a> |
  <strong>中文</strong> |
  <a href="README.ja.md">日本語</a>
</p>

> AutoShip 是一款本地优先的智能交付清道夫，帮你在不离开本机的情况下自动完成项目清理、验证、提交与产物交付。

[![PyPI](https://img.shields.io/pypi/v/autoship)](https://pypi.org/project/autoship/)
[![Python](https://img.shields.io/pypi/pyversions/autoship)](https://pypi.org/project/autoship/)
[![License](https://img.shields.io/github/license/MS33834/autoship-cli)](./LICENSE)
[![CI](https://github.com/MS33834/autoship-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/MS33834/autoship-cli/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-ms33834.github.io%2Fautoship--cli%2Fdocs-blue)](https://ms33834.github.io/autoship-cli/docs)

[查看文字版演示](docs/demo.md)

> 文字版演示已就绪：[查看 docs/demo.md](docs/demo.md)。
> asciinema 视频录制完成后将替换为以下命令生成的 `docs/demo.cast`：
>
> ```bash
> asciinema rec docs/demo.cast --command "autoship init && autoship clean && autoship commit"
> ```
>
> 官方网站：[ms33834.github.io/autoship-cli](https://ms33834.github.io/autoship-cli/)

## 路线图

> **已交付**：P1–P3 + P4-1（安全加固、插件商店、真实 AI/上传集成、CI 流水线、遥测隐私、自动化 Changelog）。已完成完整回溯审计：670 测试通过、覆盖率 87.88%、ruff + pyright + bandit 全清。已交付能力概览见 [`FEATURES.md`](./FEATURES.md)。
>
> **下一步**：P4-2 → P4-6（公开文档站、社区插件、性能/规模、安全审计、发布推广）以及 P5 向后扩展。带勾选框的实时路线图（每次更新同步双仓库）见 [`PLAN.md`](./PLAN.md)。

## 安装

### 推荐：pipx

```bash
pipx install autoship
```

### 使用 pip

```bash
pip install autoship
```

### 从源码安装

```bash
git clone https://github.com/MS33834/autoship-cli.git
cd autoship-cli
uv sync --all-extras --dev
uv run autoship --help
```

### 二进制下载

各平台预编译二进制可在 GitHub Releases 下载：

- [下载最新版本](https://github.com/MS33834/autoship-cli/releases/latest)

> 二进制由 CI 自动发布。

## 快速开始

```bash
# 初始化项目配置
autoship init

# 清理并格式化代码
autoship clean

# 生成 commit message 并提交
autoship commit

# 运行验证（以 pytest 为例）
autoship verify pytest

# 上传产物（示例：Docker 镜像）
autoship upload --target docker --image myapp --tag latest
```

## 核心特性

- **本地优先**：默认使用本地 AI 模型与本地工具链，代码无需上传云端。
- **插件化**：基于 [pluggy](https://pluggy.readthedocs.io/) 的 Hook 系统，可自由扩展清理、验证、上传等阶段。
- **插件开发 SDK**：[`autoship-sdk`](https://pypi.org/project/autoship-sdk/) 提供基类、Hook 装饰器、测试脚手架，降低插件开发门槛。
- **模型分级**：根据硬件配置与任务类型自动路由到不同层级模型，平衡速度与效果。
- **安全扫描**：提交前运行依赖漏洞与代码安全扫描，拦截潜在风险。
- **审计日志**：完整记录命令执行、模型调用与配置变更，支持结构化导出与自动清理。
- **环境诊断**：`autoship doctor` 一键检查 Python、Git、模型后端、工具链与目录权限。
- **多语言 CLI**：内置中文、英文、日文支持，`--lang zh|en|ja` 或配置 `locale` 即可切换。
- **遥测默认关闭**：匿名使用数据仅在显式开启后才会上报，尊重隐私。

## 文档

- 完整文档：[ms33834.github.io/autoship-cli/docs](https://ms33834.github.io/autoship-cli/docs)
- 本地文档：[docs/](./docs/)
- 命令参考：[docs/commands/index.md](./docs/commands/index.md)
- 配置说明：[docs/configuration.md](./docs/configuration.md)
- 插件开发指南：[docs/plugin-development.md](./docs/plugin-development.md)

## 常见问题

### AutoShip 会上传我的代码吗？

不会。默认情况下所有核心处理都在本地完成；只有当你显式配置外部模型或上传目标（如 Docker Registry、PyPI）时，才会向对应服务发送必要数据。

### 使用 AutoShip 需要联网吗？

核心命令（`init`、`clean`、`commit`、`verify`）可在离线环境下运行。`upload` 以及依赖网络搜索/外部模型的功能才需要联网。

### 如何禁用遥测？

遥测默认已关闭，无需额外操作。如需开启，可在 `.autoship.toml` 中设置 `telemetry.enabled = true`。

更多遥测字段与端点安全规则详见 [docs/telemetry.md](./docs/telemetry.md)，完整隐私政策与用户权利说明详见 [docs/privacy.md](./docs/privacy.md)。

### 如何开发自定义插件？

参考 [docs/plugin-development.md](./docs/plugin-development.md) 与示例插件 [examples/custom-plugin/](./examples/custom-plugin/)。

### AutoShip 可以用于商业项目吗？

可以。本项目基于 MIT 许可证发布，详见 [LICENSE](./LICENSE)。

## 贡献与安全

- 贡献指南：[CONTRIBUTING.md](./CONTRIBUTING.md)
- 安全报告：[SECURITY.md](./SECURITY.md)

## 许可证

MIT
