# 1.0.0 发布通告

## 中文通告

**AutoShip-CLI 1.0.0 正式发布**

我们很高兴宣布 AutoShip-CLI 首个稳定版正式上线！AutoShip 是一款本地优先、AI 辅助的代码交付工具链，帮助开发者在不将代码库上传到云端的情况下，完成清理、验证、提交、构建和发布。

### 核心亮点

- **本地 AI**：默认支持 Ollama、LM Studio 等本地模型后端，代码始终保留在本地。
- **智能提交**：基于 diff 自动生成符合 Conventional Commits 规范的提交信息。
- **插件生态**：内置安全扫描、Docker 构建、联网搜索等插件，并支持社区插件扩展。
- **企业就绪**：团队配置、审计日志、SIEM 转发、遥测白名单与隐私合规。
- **多语言 CLI**：支持英文与中文界面。

### 快速开始

```bash
pipx install autoship
autoship init
autoship clean
autoship commit
autoship verify pytest
```

### 链接

- 官网：<https://ms33834.github.io/autoship-cli/>
- 文档：<https://ms33834.github.io/autoship-cli/docs>
- GitHub：<https://github.com/MS33834/autoship-cli>
- 插件注册表：<https://ms33834.github.io/autoship-cli/registry>

---

## English Announcement

**AutoShip-CLI 1.0.0 is now available**

We are excited to announce the first stable release of AutoShip-CLI, a local-first, AI-assisted code shipping toolkit. AutoShip helps you clean, verify, commit, build, and ship code without uploading your codebase to the cloud.

### Highlights

- **Local AI**: Works with Ollama, LM Studio, and other local model backends by default.
- **Smart commits**: Generate Conventional Commits messages from staged changes.
- **Plugin ecosystem**: Built-in security scans, Docker shipping, web search, and community plugins.
- **Enterprise ready**: Team configs, structured audit logs, SIEM forwarding, telemetry allowlists, and privacy compliance.
- **Multi-language CLI**: English and Chinese interfaces supported.

### Quick start

```bash
pipx install autoship
autoship init
autoship clean
autoship commit
autoship verify pytest
```

### Links

- Website: <https://ms33834.github.io/autoship-cli/>
- Docs: <https://ms33834.github.io/autoship-cli/docs>
- GitHub: <https://github.com/MS33834/autoship-cli>
- Plugin Registry: <https://ms33834.github.io/autoship-cli/registry>

---

## 社交媒体文案

### Twitter / X

```text
🚀 AutoShip-CLI 1.0.0 is out!

Local-first, AI-assisted code shipping for Python teams.

✅ Local models (Ollama, LM Studio)
✅ Smart conventional commits
✅ Plugin ecosystem
✅ Enterprise audit & privacy controls

pipx install autoship

https://ms33834.github.io/autoship-cli/
#AI #DevTools #OpenSource
```

### 微博 / 知乎

```text
🚀 AutoShip-CLI 1.0.0 正式发布！

一款本地优先、AI 辅助的代码交付工具链：
- 默认本地模型，代码不上云
- 自动生成符合规范的提交信息
- 插件生态（安全扫描、Docker、联网搜索等）
- 企业级审计、遥测与隐私合规

pipx install autoship 即可体验。

官网：https://ms33834.github.io/autoship-cli/
文档：https://ms33834.github.io/autoship-cli/docs
```

### LinkedIn

```text
We just shipped AutoShip-CLI 1.0.0 — a local-first, AI-assisted toolkit for cleaning, verifying, committing, and shipping code.

Key features:
• Local model support (Ollama, LM Studio, vLLM, etc.)
• AI-generated conventional commits
• Extensible plugin system with built-in security scans
• Team configs, audit logs, and privacy-first telemetry

Try it: pipx install autoship
Read more: https://ms33834.github.io/autoship-cli/
```

---

## 发布邮件模板

**主题**：AutoShip-CLI 1.0.0 正式发布

正文：

```text
Hi all,

AutoShip-CLI 1.0.0 首个稳定版已发布。

AutoShip 是一款本地优先、AI 辅助的代码交付工具链，旨在帮助开发团队在不泄露代码的前提下，提升提交、验证、构建和发布的效率。

主要特性：
- 本地 AI 模型支持（Ollama / LM Studio / vLLM 等）
- 智能提交信息生成
- 内置安全扫描、Docker 构建、联网搜索插件
- 插件注册表与社区扩展
- 团队配置、审计日志、隐私合规遥测

安装方式：pipx install autoship
文档：https://ms33834.github.io/autoship-cli/docs
GitHub：https://github.com/MS33834/autoship-cli

欢迎试用并反馈问题。

AutoShip Team
```
