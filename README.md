# AutoShip-CLI

> 本地优先的智能交付清道夫（Local-first intelligent delivery assistant）

AutoShip-CLI 帮助开发者自动化项目开发后的清理、验证、提交与上传流程。所有核心处理默认在本地完成，代码无需上传云端。

## 核心特性

- **本地优先**：默认使用本地 AI 模型与本地工具链，避免代码泄露。
- **插件化**：基于 `pluggy` 的 Hook 系统，可自由扩展。
- **模型分级**：根据硬件与任务自动路由到不同层级模型。
- **安全可靠**：审计日志、凭证加密、插件沙箱、提交前安全扫描。

## 快速开始

```bash
# 安装
pipx install autoship

# 初始化项目
autoship init

# 清理并格式化代码
autoship clean

# 生成 commit message 并提交
autoship commit
```

## 开发

本项目使用 [uv](https://docs.astral.sh/uv/) 作为包管理工具。

```bash
uv sync --all-extras
uv run pytest
```

## 许可证

MIT
