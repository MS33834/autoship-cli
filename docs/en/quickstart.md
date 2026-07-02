---
title: Quickstart
---
# Quickstart

> This guide walks you through AutoShip's core workflow in 5 minutes. AutoShip is local-first by default — clean/verify/commit never leave your machine.

## Prerequisites

- Python ≥ 3.10
- [pipx](https://pypa.github.io/pipx/) or [uv](https://docs.astral.sh/uv/)
- Git, and the current directory is a Git repository
- (Optional, to try AI-powered fixes) [Ollama](https://ollama.com/) is running

## Installation

```bash
pipx install autoship
```

## 5-Minute No-AI Version

```bash
# 1. Initialize configuration
autoship init --yes

# 2. Clean code (remove unused imports, format)
autoship clean --yes

# 3. Generate commit message and commit
autoship commit

# 4. Run tests to verify
autoship verify pytest

# 5. Preview upload (does not actually upload)
autoship upload --target pypi --dry-run
```

> `upload --dry-run` is a preview only. Real uploads require PyPI credentials, see [Upload Command Reference](commands/upload.md).

## +5-Minute AI Version

If you want to try `verify --fix` auto-repair:

```bash
# 1. Install and start Ollama, pull a small model
ollama pull qwen2.5-coder:1.5b

# 2. Configure AutoShip to use Ollama (in .autoship.toml)
# [model]
# backend = "ollama"

# 3. Verify and auto-fix
autoship verify --fix pytest
```

## Next Steps

- [Command Reference](commands/index.md)
- [Configuration](configuration.md)
- [Model Configuration](models.md)
- [Plugin Development](plugin-development.md)
