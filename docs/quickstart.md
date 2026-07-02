---
title: 快速开始
---
# 快速开始

> 本指南带你 5 分钟跑通 AutoShip 核心流程。AutoShip 默认本地优先——clean/verify/commit 全程不离开本机。

## 前置条件

- Python ≥ 3.10
- [pipx](https://pypa.github.io/pipx/) 或 [uv](https://docs.astral.sh/uv/)
- Git，且当前目录是 Git 仓库
- （可选，体验 AI 修复）[Ollama](https://ollama.com/) 已运行

## 安装

```bash
pipx install autoship
```

## 5 分钟无 AI 版

```bash
# 1. 初始化配置
autoship init --yes

# 2. 清理代码（删除无用 import、格式化）
autoship clean --yes

# 3. 生成 commit message 并提交
autoship commit

# 4. 运行测试验证
autoship verify pytest

# 5. 预览上传（不实际上传）
autoship upload --target pypi --dry-run
```

> `upload --dry-run` 仅预览，真实上传需配置 PyPI 凭证，详见 [上传命令参考](commands/upload.md)。

## +5 分钟带 AI 版

如果你想体验 `verify --fix` 自动修复：

```bash
# 1. 安装并启动 Ollama，拉取小模型
ollama pull qwen2.5-coder:1.5b

# 2. 配置 AutoShip 使用 Ollama（在 .autoship.toml 里）
# [model]
# backend = "ollama"

# 3. 验证并自动修复
autoship verify --fix pytest
```

## 下一步

- [命令参考](commands/index.md)
- [配置说明](configuration.md)
- [模型配置](models.md)
- [插件开发](plugin-development.md)
