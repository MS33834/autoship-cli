---
title: Contributing
---
## Repository Notes

**This repository uses GitHub as the primary repository and GitCode as a mirror.**

- Primary repository: https://github.com/MS33834/autoship-cli
- GitCode mirror: https://gitcode.com/badhope/autoship-cli

Please submit Issues and Pull Requests directly to the **GitHub primary repository**. GitCode is only used for code mirroring and does not handle Issues/PRs.

---

# Contributing Guide

Thank you for your interest in AutoShip-CLI! We welcome and encourage community contributions.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](https://github.com/MS33834/autoship-cli/blob/main/CODE_OF_CONDUCT.md).

## How to Contribute

- Report bugs: Please use GitHub Issues and include reproduction steps, environment information, and a minimal reproduction example.
- Make suggestions: Share your ideas via GitHub Discussions.
- Submit code: Fork the repository, create a feature branch, and submit a Pull Request.

## Development Environment

This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies.

```bash
uv sync --all-extras --dev
uv run pytest
```

## Code Standards

- Use [ruff](https://docs.astral.sh/ruff/) for formatting and linting.
- Use [pyright](https://microsoft.github.io/pyright/) for strict type checking.
- Commit messages should be in English and follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
- New features must include tests, keeping coverage no lower than 85%.

## Submitting a Pull Request

1. Make sure all checks pass: `uv run ruff check src tests`, `uv run pyright`, `uv run pytest`.
2. Run the security scan: `uv run bandit -r src -ll`.
3. Explain the reason for the change, its impact scope, and how it was tested in the PR description.
4. Wait for maintainer review and make changes if necessary.

## Submitting Plugins to the Registry

We welcome third-party plugins! Please follow this process to submit:

1. Create a plugin project using [`autoship-sdk`](https://pypi.org/project/autoship-sdk/) and publish it to PyPI.
2. Create an issue on GitHub using the **Plugin Submission** template.
3. Maintainers will review based on the following checklist:
   - The plugin follows the AutoShip hook spec and does not perform unauthorized operations.
   - It includes a README, an open-source license, and basic tests.
   - The name does not conflict with existing plugins and follows the `autoship-*` naming convention.
   - When requesting `verified`, a SHA256 checksum or GPG signature must be provided.
4. After approval, the plugin is added to `src/autoship/registry/plugins.json`
   and automatically appears in the [Plugin Registry Web UI](https://autoship-cli.github.io/autoship-registry/).

## License

By contributing code, you agree that your contributions will be licensed under the same [MIT](https://github.com/MS33834/autoship-cli/blob/main/LICENSE) license as the project.
