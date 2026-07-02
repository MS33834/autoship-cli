# AutoShip-CLI

<p align="right">
  <strong>English</strong> |
  <a href="README.zh.md">中文</a> |
  <a href="README.ja.md">日本語</a>
</p>

> AutoShip is a local-first intelligent delivery janitor. It helps you clean, verify, commit, and ship project artifacts without leaving your machine.

[![PyPI](https://img.shields.io/pypi/v/autoship)](https://pypi.org/project/autoship/)
[![Python](https://img.shields.io/pypi/pyversions/autoship)](https://pypi.org/project/autoship/)
[![License](https://img.shields.io/github/license/MS33834/autoship-cli)](./LICENSE)
[![CI](https://github.com/MS33834/autoship-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/MS33834/autoship-cli/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-ms33834.github.io%2Fautoship--cli%2Fdocs-blue)](https://ms33834.github.io/autoship-cli/docs)

[View text demo](docs/demo.md)

> Demo coming soon — check out the [demo script](docs/demo.md).
> Once the asciinema video is recorded, this section will be replaced by `docs/demo.cast`:
>
> ```bash
> asciinema rec docs/demo.cast --command "autoship init && autoship clean && autoship commit"
> ```
>
> Official site: [ms33834.github.io/autoship-cli](https://ms33834.github.io/autoship-cli/)

## Roadmap

> **Shipped**: P1–P3 + P4-1 (security hardening, plugin store, real AI/upload
> integration, CI pipeline, telemetry privacy, automated changelog). A full
> back-rotation audit passed: 670 tests green, 87.88% coverage, ruff + pyright
> + bandit clean. See [`FEATURES.md`](./FEATURES.md) for the delivered
> capability summary.
>
> **Next**: P4-2 → P4-6 (public docs site, community plugins, perf/scale,
> security audit, launch) and the P5 forward expansion. The living roadmap
> with checkboxes — updated and mirrored to both remotes on every change —
> lives in [`PLAN.md`](./PLAN.md).

## Installation

### Recommended: pipx

```bash
pipx install autoship
```

### Using pip

```bash
pip install autoship
```

### From source

```bash
git clone https://github.com/MS33834/autoship-cli.git
cd autoship-cli
uv sync --all-extras --dev
uv run autoship --help
```

### Binary download

Pre-built binaries for all platforms are available from GitHub Releases:

- [Download latest release](https://github.com/MS33834/autoship-cli/releases/latest)

> Binaries are published automatically by CI.

## Quick Start

```bash
# Initialize project configuration
autoship init

# Clean and format code
autoship clean

# Generate commit message and commit
autoship commit

# Run verification (pytest example)
autoship verify pytest

# Upload artifacts (example: Docker image)
autoship upload --target docker --image myapp --tag latest
```

## Core Features

- **Local-first**: Uses local AI models and local toolchains by default; code does not leave your machine.
- **Plugin system**: Hook-based architecture powered by [pluggy](https://pluggy.readthedocs.io/) for extending clean, verify, upload, and other phases.
- **Plugin development SDK**: [`autoship-sdk`](https://pypi.org/project/autoship-sdk/) provides base classes, hook decorators, and testing helpers.
- **Model tiers**: Automatically routes tasks across different model tiers based on hardware and task type.
- **Security scanning**: Runs dependency vulnerability and code security scans before commit.
- **Audit logging**: Records command execution, model calls, and configuration changes with structured export and auto cleanup.
- **Environment diagnostics**: `autoship doctor` checks Python, Git, model backends, toolchains, and directory permissions in one command.
- **Multi-language CLI**: Built-in English, Chinese, and Japanese support via `--lang zh|en|ja` or the `locale` config option.
- **Telemetry off by default**: Anonymous usage data is only reported after explicit opt-in.

## Documentation

- Full docs: [ms33834.github.io/autoship-cli/docs](https://ms33834.github.io/autoship-cli/docs)
- Local docs: [docs/](./docs/)
- Command reference: [docs/commands/index.md](./docs/commands/index.md)
- Configuration: [docs/configuration.md](./docs/configuration.md)
- Plugin development: [docs/plugin-development.md](./docs/plugin-development.md)

## FAQ

### Does AutoShip upload my code?

No. All core processing runs locally by default; only when you explicitly configure an external model or upload target (such as Docker Registry or PyPI) will necessary data be sent to those services.

### Does AutoShip require internet access?

Core commands (`init`, `clean`, `commit`, `verify`) can run offline. `upload` and features that depend on web search or external models require internet access.

### How do I disable telemetry?

Telemetry is disabled by default, so no extra action is needed. To enable it, set `telemetry.enabled = true` in `.autoship.toml`.

For telemetry fields and endpoint security rules, see [docs/telemetry.md](./docs/telemetry.md). For the full privacy policy and user rights, see [docs/privacy.md](./docs/privacy.md).

### How do I develop a custom plugin?

See [docs/plugin-development.md](./docs/plugin-development.md) and the example plugin at [examples/custom-plugin/](./examples/custom-plugin/).

### Can AutoShip be used for commercial projects?

Yes. This project is released under the MIT License. See [LICENSE](./LICENSE).

## Contributing and Security

- Contributing guide: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Security report: [SECURITY.md](./SECURITY.md)

## License

MIT
