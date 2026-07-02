# AutoShip CLI

> 你的代码，从不上云

<div align="center">

**本地优先的智能交付助手**

清理 · 验证 · 提交 · 上传，全程不离开你的机器

```bash
pipx install autoship
```

[5 分钟快速开始](quickstart.md) · [为什么选 AutoShip](why-autoship.md)

</div>

---

## 核心特性

- **本地优先**：默认使用本地 AI 模型与本地工具链，避免代码泄露。
- **插件化**：基于 [pluggy](https://pluggy.readthedocs.io/) 的 Hook 系统，可自由扩展。
- **模型分级**：根据硬件与任务自动路由到不同层级模型。
- **安全可靠**：审计日志、凭证加密、插件沙箱、提交前安全扫描。

## 安装

推荐使用 [pipx](https://pypa.github.io/pipx/) 安装，以便隔离依赖：

```bash
pipx install autoship
```

或使用 [uv](https://docs.astral.sh/uv/)：

```bash
uv tool install autoship
```

开发者可直接克隆仓库并使用 uv：

```bash
git clone https://github.com/MS33834/autoship-cli.git
cd autoship-cli
uv sync --all-extras --dev
```

## 快速开始

在项目根目录执行：

```bash
# 初始化 AutoShip 配置
autoship init

# 清理并格式化代码
autoship clean

# 生成 commit message 并提交
autoship commit

# 运行测试验证
autoship verify pytest

# 上传产物（示例：Docker）
autoship upload --target docker --image myapp --tag latest
```

## 全局选项

所有命令都支持以下全局选项：

| 选项 | 说明 |
|---|---|
| `-v, --verbose` | 输出更详细的日志 |
| `-n, --dry-run` | 仅预览操作，不真正执行 |
| `-y, --yes` | 跳过交互式确认 |
| `-c, --config PATH` | 指定配置文件路径 |

## 下一步

- 查看 [命令参考](./commands/index.md) 了解每个命令的详细用法。
- 查看 [配置说明](configuration.md) 了解 `.autoship.toml` 配置项。
- 查看 [插件](plugins.md) 与 [插件开发指南](plugin-development.md) 了解如何扩展 AutoShip。
