# Changelog

This document follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format and adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-19

### Added

- First stable release.
- Added community health files and issue templates to collect production feedback.

### Changed

- `autoship` version bumped to `1.0.0`.
- `autoship-sdk` version bumped to `1.0.0` and depends on `autoship>=1.0.0`.

### Fixed

- All GitHub Actions workflows updated to assume paths based on the repository root, removing the previous `autoship-cli/` subdirectory prefix.
- `release.yml` now builds and publishes `autoship-sdk` to PyPI as well.

## [1.0.0-rc.1] - 2026-06-19

### Added

- CLI internationalization (i18n), supporting English and Chinese.
  - Use `--lang zh|en` or set `locale = "zh"` in `.autoship.toml`.
  - Automatically detects the system language and falls back to English by default.
- `autoship doctor` diagnostic command: checks Python, Git, model backends, cleanup toolchains, plugin dependencies, and audit/telemetry directory permissions.
- `autoship audit export` and `autoship audit cleanup` commands, supporting structured export of audit logs and retention management.
- Official plugin registry index `src/autoship/registry/plugins.json`, supporting `autoship plugin search` and `autoship plugin install`.
- `autoship-sdk` plugin development kit (located in `autoship-sdk/`):
  - `Plugin` base class and `hook` decorator.
  - `PluginTestHarness` for isolated hook testing.
  - `create_plugin` scaffolding for creating new plugin projects.
- `website/` static official website and GitHub Pages deployment workflow.
- Team-level configuration support via `.autoship.team.toml`.
- Environment variables with the `AUTOSHIP_*` prefix to override all configuration options.

### Changed

- `autoship` version bumped to `1.0.0-rc.1`.
- `autoship-sdk` version bumped to `1.0.0-rc.1` and depends on `autoship>=1.0.0rc1`.

### Fixed

- Fixed mypy/pyright compatibility issues in `ollama.py`, `registry_index.py`, `config_center.py`, `hardware_profiler.py`, and `hook_dispatcher.py`.

## [0.2.0-beta.1] - 2026-06-18

### Added

- Boundary tests and error injection covering the model layer, Git layer, toolchain layer, plugin layer, and file/resource layer.
- Performance benchmark framework `benchmarks/benchmark.py`, supporting metrics such as startup time, clean execution time, and idle memory.
- CI/CD multi-platform packaging: Linux/macOS/Windows single-file executables, SHA256 checksums, and SBOMs.
- `benchmark.yml` workflow supporting manual and PR-triggered performance regression checks.
- MkDocs Material documentation site with automatic GitHub Pages deployment.
- Optional telemetry and error reporting, disabled by default, collecting only command/duration/exit code/exception type (no code content).

### Fixed

- `OllamaGateway.chat` now correctly converts HTTP errors, JSON parsing errors, and timeouts into `ModelGatewayError`.
- The `--check` argument of the `clean` command uses a real boolean default value when invoked directly.

### Changed

- Development dependencies added `pyinstaller>=6.0.0` and `mkdocs-material>=9.0.0`.

## [0.1.0] - 2026-06-18

### Added

- Initialized AutoShip-CLI core commands: `init`, `clean`, `commit`, `verify`, `upload`, `plugin`.
- Plugin system based on [pluggy](https://pluggy.readthedocs.io/), supporting `pre_*`, `post_*`, and `on_error` lifecycle hooks.
- Local-first AI model routing, supporting Ollama, LM Studio, llama.cpp, and vLLM backends.
- Hardware awareness: automatically recommends model tiers based on CPU/GPU/memory.
- Official built-in plugins:
  - `security-scan`: runs bandit/gitleaks/osv-scanner security scans before commits.
  - `docker-ship`: automatically builds/pushes images on `upload --target docker`.
  - `web-search`: searches the web for error context when `verify --fix` fails.
- Audit log system that records key CLI operations.
- Plugin trust levels and local registry management (`builtin`/`verified`/`community`/`untrusted`).
- Upload adapters supporting PyPI, Docker, and GitHub.
- End-to-end (E2E) tests and boundary scenario coverage.
- Performance benchmarks and result recording (`benchmarks/`).
- Complete Chinese MkDocs Material documentation site.
- GitHub Actions documentation auto-deployment workflow.

### Changed

- Unified Typer CLI entry point and global options (`--verbose`, `--dry-run`, `--yes`, `--config`).
- Uses Pydantic to define the `.autoship.toml` configuration model.

### Security

- Security scanning integrated bandit and pip-audit.
- Credentials are not written to logs by default.
- Plugins run through the hook mechanism, following the principle of least privilege.

[1.0.0]: https://github.com/MS33834/autoship-cli/releases/tag/v1.0.0
[1.0.0-rc.1]: https://github.com/MS33834/autoship-cli/releases/tag/v1.0.0-rc.1
[0.2.0-beta.1]: https://github.com/MS33834/autoship-cli/releases/tag/v0.2.0-beta.1
[0.1.0]: https://github.com/MS33834/autoship-cli/releases/tag/v0.1.0
