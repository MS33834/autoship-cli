---
title: AutoShip CLI
---
# AutoShip CLI

> Your code, never in the cloud

<div align="center">

**Local-first intelligent delivery assistant**

Clean · Verify · Commit · Upload — without leaving your machine

```bash
pipx install autoship
```

[5-minute Quick Start](quickstart.md) · [Why AutoShip](why-autoship.md)

</div>

---

## Core Features

- **Local-first**: Uses local AI models and local toolchains by default to avoid code leaks.
- **Plugin-based**: Hook system powered by [pluggy](https://pluggy.readthedocs.io/) for easy extension.
- **Model tiers**: Automatically routes tasks across different model tiers based on hardware and task type.
- **Safe and reliable**: Audit logging, credential encryption, plugin sandbox, and pre-commit security scans.

## Installation

We recommend installing with [pipx](https://pypa.github.io/pipx/) to keep dependencies isolated:

```bash
pipx install autoship
```

Or use [uv](https://docs.astral.sh/uv/):

```bash
uv tool install autoship
```

Developers can clone the repository and use uv directly:

```bash
git clone https://github.com/MS33834/autoship-cli.git
cd autoship-cli
uv sync --all-extras --dev
```

## Quick Start

Run these commands in your project root:

```bash
# Initialize AutoShip configuration
autoship init

# Clean and format code
autoship clean

# Generate commit message and commit
autoship commit

# Run verification
autoship verify pytest

# Upload artifacts (example: Docker)
autoship upload --target docker --image myapp --tag latest
```

## Global Options

All commands support the following global options:

| Option | Description |
|---|---|
| `-v, --verbose` | Output more detailed logs |
| `-n, --dry-run` | Preview actions without actually executing them |
| `-y, --yes` | Skip interactive confirmations |
| `-c, --config PATH` | Specify a custom configuration file path |

## Next Steps

- See the [Command Reference](../commands/index.md) for detailed usage of each command.
- See [Configuration](../configuration.md) for `.autoship.toml` options.
- See [Plugins](../plugins.md) and the [Plugin Development Guide](../plugin-development.md) to learn how to extend AutoShip.
