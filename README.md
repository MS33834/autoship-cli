# AutoShip-CLI

> AutoShip 是一款本地优先的智能交付清道夫，帮你在不离开本机的情况下自动完成项目清理、验证、提交与产物交付。

[![PyPI](https://img.shields.io/pypi/v/autoship)](https://pypi.org/project/autoship/)
[![Python](https://img.shields.io/pypi/pyversions/autoship)](https://pypi.org/project/autoship/)
[![License](https://img.shields.io/github/license/autoship-cli/autoship-cli)](./LICENSE)
[![CI](https://github.com/autoship-cli/autoship-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/autoship-cli/autoship-cli/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-docs.autoship.dev-blue)](https://docs.autoship.dev)

[查看文字版演示](docs/demo.md)

> 文字版演示已就绪：[查看 docs/demo.md](docs/demo.md)。
> asciinema 视频录制完成后将替换为以下命令生成的 `docs/demo.cast`：
>
> ```bash
> asciinema rec docs/demo.cast --command "autoship init && autoship clean && autoship commit"
> ```
>
> 官方网站：[autoship.dev](https://autoship.dev)

## 当前计划

> 详见 [TASKS.md](./TASKS.md)。下面把主要进度同步到 README，避免会话丢失。

| 阶段 | 任务 | 状态 |
|------|------|------|
| P1 | 注册表索引签名/完整性校验 (P1-1) | ✅ 已完成 |
| P1 | 插件安装 sha256/signature 校验 (P1-2) | ✅ 已完成 |
| P1 | 审计日志脱敏策略增强 (P1-3) | ✅ 已完成 |
| P1 | `commit` 命令 EDITOR 校验 (P1-4) | ✅ 已完成 |
| P1 | `verify` 失败日志脱敏与权限收紧 (P1-5) | ✅ 已完成 |
| P2 | 文件权限收紧 (P2-1) | ✅ 已完成 |
| P2 | `fix` 命令读取文件路径限制 (P2-2) | ✅ 已完成 |
| P2 | 外部工具 PATH 防护 (P2-3) | ✅ 已完成 |
| P2 | `docker_ship` 插件 `build_args` 校验 (P2-4) | ✅ 已完成 |
| P2 | 环境变量覆盖配置白名单 (P2-5) | ✅ 已完成 |
| P2 | SIEM 转发失败告警 (P2-6) | ✅ 已完成 |
| P2 | Telemetry 端点校验 (P2-7) | ✅ 已完成 |
| P2 | 模型网关错误信息脱敏 (P2-8) | ✅ 已完成 |
| P3 | AI 路径真实后端联测 (P3-1) | ✅ 已完成 |
| P3 | 真实上传集成（PyPI / Docker）(P3-2) | ✅ 已完成 |
| P3 | 安装包与分发验证 (P3-3) | ✅ 已完成 |
| P3 | 完整命令参考文档 (P3-4) | ✅ 已完成 |
| P3 | GitHub Actions CI 流水线 (P3-5) | ✅ 已完成 |
| P3 | 错误消息与 UX 打磨 (P3-6) | ✅ 已完成 |
| P3 | 遥测与隐私合规 (P3-7) | ✅ 已完成 |
| P3 | 插件商店与发布流程 (P3-8) | ⏳ 待开始 |

下一步：**继续推进 P3-8 插件商店与发布流程**。

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
git clone https://github.com/autoship-cli/autoship-cli.git
cd autoship-cli
uv sync --all-extras --dev
uv run autoship --help
```

### 二进制下载

各平台预编译二进制可在 GitHub Releases 下载：

- [下载最新版本](https://github.com/autoship-cli/autoship-cli/releases/latest)

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
- **多语言 CLI**：内置中英文支持，`--lang zh|en` 或配置 `locale` 即可切换。
- **遥测默认关闭**：匿名使用数据仅在显式开启后才会上报，尊重隐私。

## 文档

- 完整文档：[docs.autoship.dev](https://docs.autoship.dev)
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
