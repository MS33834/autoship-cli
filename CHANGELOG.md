# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0-beta.1] - 2026-06-18

### Added

- Boundary tests and error injection for the model, Git, toolchain, plugin, and file/resource layers.
- Performance benchmark framework at `benchmarks/benchmark.py` covering startup time,
  `clean` execution time, and idle memory usage.
- CI/CD multi-platform builds: Linux/macOS/Windows single-file executables, SHA256 checksums,
  and SBOM generation.
- `benchmark.yml` workflow for manual and pull-request performance regression checks.
- MkDocs Material documentation site with automatic GitHub Pages deployment.
- Optional telemetry and error reporting, disabled by default, collecting only
  command name, duration, exit code, and exception type (no source code).

### Fixed

- `OllamaGateway.chat` now correctly converts HTTP errors, JSON parse errors, and timeouts
  into `ModelGatewayError`.

### Changed

- Development dependencies now include `pyinstaller>=6.0.0` and `mkdocs-material>=9.0.0`.

## [0.1.0] - 2026-06-18

### Added

- Initial AutoShip-CLI core commands: `init`, `clean`, `commit`, `verify`, `upload`, `plugin`.
- Plugin system based on [pluggy](https://pluggy.readthedocs.io/) supporting `pre_*`, `post_*`,
  and `on_error` lifecycle hooks.
- Local-first AI model routing supporting Ollama, LM Studio, llama.cpp, and vLLM backends.
- Hardware-aware model tier recommendations based on CPU/GPU/memory.
- Official built-in plugins:
  - `security-scan`: pre-commit security scanning with bandit/gitleaks/osv-scanner.
  - `docker-ship`: automatic Docker image build/push for `upload --target docker`.
  - `web-search`: web search context for `verify --fix` failures.
- Audit logging for key CLI operations.
- Plugin trust levels and local registry management.
- Upload adapters for PyPI, Docker, and GitHub.
- End-to-end and boundary scenario tests.
- Performance benchmarks and result recording.
- Full Chinese MkDocs Material documentation site.
- GitHub Actions documentation deployment workflow.

### Changed

- Unified Typer CLI entry with global options (`--verbose`, `--dry-run`, `--yes`, `--config`).
- Pydantic-based `.autoship.toml` configuration models.

### Security

- Integrated bandit and pip-audit security scanning.
- Credentials excluded from logs by default.
- Plugins run through a hook mechanism following least-privilege principles.
