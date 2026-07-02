---
title: 1.0.0 Release Announcement
---
# 1.0.0 Release Announcement

## Chinese Announcement

**AutoShip-CLI 1.0.0 Officially Released**

We are pleased to announce the official release of the first stable version of AutoShip-CLI! AutoShip is a local-first, AI-assisted code shipping toolkit that helps developers clean, verify, commit, build, and ship without uploading their codebase to the cloud.

### Core Highlights

- **Local AI**: Supports local model backends such as Ollama and LM Studio by default; code always stays local.
- **Smart Commits**: Automatically generates Conventional Commits-compliant commit messages based on diffs.
- **Plugin Ecosystem**: Built-in plugins for security scanning, Docker builds, web search, and support for community plugin extensions.
- **Enterprise Ready**: Team configuration, audit logs, SIEM forwarding, telemetry allowlists, and privacy compliance.
- **Multi-language CLI**: Supports English and Chinese interfaces.

### Quick Start

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

## Social Media Copy

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

### Weibo / Zhihu

```text
🚀 AutoShip-CLI 1.0.0 is officially released!

A local-first, AI-assisted code shipping toolkit:
- Local models by default, code never leaves your machine
- Automatically generates spec-compliant commit messages
- Plugin ecosystem (security scanning, Docker, web search, etc.)
- Enterprise-grade audit, telemetry, and privacy compliance

Install with pipx install autoship to try it out.

Website: https://ms33834.github.io/autoship-cli/
Docs: https://ms33834.github.io/autoship-cli/docs
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

## Release Email Template

**Subject**: AutoShip-CLI 1.0.0 Officially Released

Body:

```text
Hi all,

The first stable release of AutoShip-CLI 1.0.0 is now available.

AutoShip is a local-first, AI-assisted code shipping toolkit designed to help development teams improve the efficiency of committing, verifying, building, and shipping without leaking code.

Key features:
- Local AI model support (Ollama / LM Studio / vLLM, etc.)
- Smart commit message generation
- Built-in security scanning, Docker build, and web search plugins
- Plugin registry and community extensions
- Team configuration, audit logs, and privacy-compliant telemetry

Install: pipx install autoship
Docs: https://ms33834.github.io/autoship-cli/docs
GitHub: https://github.com/MS33834/autoship-cli

Please try it out and report any issues.

AutoShip Team
```
