# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- P4-2 public documentation site: trilingual (zh/en/ja) Quickstart, Why AutoShip
  comparison page, Troubleshooting guide, and Known Issues page.
- MkDocs search configured with CJK language support (en/ja) for Chinese and
  Japanese keyword search.
- Landing page hero with value proposition ("your code, never in the cloud"),
  install command block, and CTA buttons on all three locale index pages.
- `robots.txt` for SEO, served from the GitHub Pages root.
- CI docs job: `mkdocs build --strict`, `check_i18n_sync.py`,
  `sync_command_docs.py --check`, and `scan_docs_secrets.py --check` as gates.
- `website.yml` deploy build now runs `mkdocs build --strict` (double gate with
  the CI docs job).
- Nightly external link checker (lychee) workflow for docs/website/README links.
- "Remote repository health check" section in CONTRIBUTING.md — mandatory
  before/after every phase: PR/Issue triage, branch cleanup, CI green check,
  GitCode mirror sync, Dependabot advisory review.
- `docs/reviews/p4-2-public-docs-site-plan.md` detailed execution plan with
  multi-role review record (architect/PM/dev-lead/security/test).

### Changed

- Unified upgrade of 6 GitHub Actions across all workflows: `setup-uv` v3→v7,
  `upload-artifact` v4→v7, `download-artifact` v4→v8, `setup-node` v4→v6,
  `deploy-pages` v4→v5 (closes Dependabot PRs #38–#42).
- `website.yml` deploy build runs `mkdocs build --strict`.
- `docs/demo.md` recording script aligned with Quickstart command sequence;
  added redaction showcase segment and recording environment spec.
- All `docs/en/` and `docs/ja/` markdown files now carry `title:` front matter
  so the navigation bar shows localized labels instead of Chinese.
- Fixed 4 cross-locale broken links in `website/index*.html` and
  `plugins*.html` (en/ja pages were linking to the zh default locale).

### Fixed

- `mkdocs build --strict` now passes with 0 warnings (CODE_OF_CONDUCT.md and
  LICENSE.md links converted to absolute GitHub URLs).
- i18n structural parity: `demo.md`, `commands/clean.md`, `commands/metrics.md`
  en/ja aligned to zh heading/code-block counts.
- `scripts/validate_registry.py` and `scripts/release_changelog.py` pyright
  strict-mode issues resolved.

## [1.0.0] - 2026-06-19

### Added

- Official 1.0 stable release.
- Community health files and issue templates for production feedback.

### Changed

- `autoship` version bumped to `1.0.0`.
- `autoship-sdk` version bumped to `1.0.0` and depends on `autoship>=1.0.0`.

### Fixed

- All GitHub Actions workflows updated to use repository-root paths instead of
  the previous `autoship-cli/` subdirectory assumption.
- `release.yml` now also builds and publishes `autoship-sdk` to PyPI.

## [1.0.0-rc.1] - 2026-06-19

### Added

- CLI internationalization (i18n) with English and Chinese locales.
  - Use `--lang zh|en` or set `locale = "zh"` in `.autoship.toml`.
  - Auto-detection of system locale with fallback to English.
- `autoship doctor` diagnostic command: checks Python, Git, model backends,
  clean toolchain, plugin dependencies, and audit/telemetry directory permissions.
- `autoship audit export` and `autoship audit cleanup` commands for structured
  audit log export and retention management.
- Official plugin registry index at `src/autoship/registry/plugins.json` with
  `autoship plugin search` and `autoship plugin install` support.
- `autoship-sdk` plugin development kit under `autoship-sdk/`:
  - `Plugin` base class and `hook` decorator.
  - `PluginTestHarness` for isolated hook testing.
  - `create_plugin` scaffold for new plugin projects.
- Static official website at `website/` with GitHub Pages deployment workflow.
- Team-level configuration support via `.autoship.team.toml`.
- Environment variable overrides for all config keys using `AUTOSHIP_*` prefix.

### Changed

- `autoship` version bumped to `1.0.0-rc.1`.
- `autoship-sdk` version bumped to `1.0.0-rc.1` and depends on `autoship>=1.0.0rc1`.

### Fixed

- mypy/pyright compatibility issues in `ollama.py`, `registry_index.py`,
  `config_center.py`, `hardware_profiler.py`, and `hook_dispatcher.py`.

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
- The `--check` argument of the `clean` command uses a real boolean default value when
  invoked directly.

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
