---
title: Release Checklist
---
# Release Checklist

This checklist guides AutoShip-CLI maintainers through completing an official or pre-release version. Before release, at least two maintainers must cross-review and check off all items.

---

## 1. Version & Changelog

- [ ] Confirm the version number follows [SemVer](https://semver.org/).
  - Stable release: `MAJOR.MINOR.PATCH`, e.g. `1.0.0`.
  - Pre-release: append `-alpha.N`, `-beta.N`, or `-rc.N`, e.g. `1.1.0-rc.1`.
- [ ] The root [`CHANGELOG.md`](https://github.com/MS33834/autoship-cli/blob/main/CHANGELOG.md) is generated automatically by the Release workflow after the GitHub Release is created (`scripts/release_changelog.py` → `update-changelog` job); after release, return to `main` and review the auto-written version section.
  - Version section format: `Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security` subsections, with the release date (UTC+8).
- [ ] Update the documentation [`changelog.md`](./changelog.md) (zh/en/ja locales) in sync.
- [ ] Confirm that `project.version` in `pyproject.toml` matches the target version.
- [ ] Confirm that the version number and dependency constraints in `autoship-sdk/pyproject.toml` are updated in sync.

## 2. Code Quality Gates

Run and pass locally:

```bash
uv run ruff check src tests dogfood benchmarks
uv run ruff format --check src tests dogfood benchmarks
uv run pyright
uv run pytest -q
uv run pytest autoship-sdk/tests -q
uv run bandit -r src -ll
uv run pip-audit --desc
```

- [ ] ruff lint passes
- [ ] ruff format check passes
- [ ] pyright type check passes
- [ ] autoship unit tests pass (coverage ≥ 85%)
- [ ] autoship-sdk tests pass
- [ ] bandit security scan has no medium/high severity issues
- [ ] pip-audit dependency vulnerability scan has no unfixed issues

## 3. Integration & Performance Tests

```bash
uv run python dogfood/dogfood.py
uv run python benchmarks/benchmark.py
```

- [ ] dogfood smoke test passes
- [ ] benchmark regression test passes, no performance degradation

## 4. Documentation & Website

- [ ] Command reference documentation is consistent with actual CLI behavior.
- [ ] Installation/quick start steps in `docs/index.md` and `README.md` are reproducible.
- [ ] Data collection scope in `docs/privacy.md` and `docs/telemetry.md` is accurate.
- [ ] Preview the MkDocs site locally: `uv run mkdocs serve`, confirm navigation and links work.
- [ ] Official website `website/` build passes: `cd website && npm install && npm run build`.

## 5. Signing Keys & Credentials

- [ ] The PGP private key used to sign `verified` plugins is valid and not expired.
- [ ] PyPI/TestPyPI release token or Trusted Publishing configuration is valid.
- [ ] GitHub Actions environment `pypi` / `testpypi` approval rules are configured.

## 6. Release Execution

### 6.1 Create a Git Tag

```bash
git switch main
git pull origin main
git tag -a v<X.Y.Z> -m "Release v<X.Y.Z>"
git push origin v<X.Y.Z>
```

- [ ] Tag name matches the version number (e.g. `v1.0.0`).
- [ ] Tag points to the latest commit on the `main` branch.

### 6.2 Trigger the Release Workflow

Pushing the tag automatically triggers [`.github/workflows/release.yml`](https://github.com/MS33834/autoship-cli/blob/main/.github/workflows/release.yml):

- [ ] `pypi` / `testpypi` auto-routing is correct (pre-release tags go to TestPyPI).
- [ ] `autoship` and `autoship-sdk` wheels are uploaded successfully.
- [ ] Multi-platform binaries and SHA256 checksums are generated successfully.
- [ ] GitHub Release Notes are auto-generated and include binary artifacts.

## 7. Post-Release Verification

- [ ] PyPI/TestPyPI page shows the new version.
- [ ] `pip install autoship==<X.Y.Z>` installs successfully.
- [ ] Download the binary from the GitHub Release; `autoship --help` and `autoship doctor` run normally.
- [ ] Official documentation site `https://ms33834.github.io/autoship-cli/docs` is refreshed.
- [ ] Official website `https://ms33834.github.io/autoship-cli/` is refreshed (if website changes are involved).

## 8. Security Announcements & Communication

If this release includes security fixes:

- [ ] Update supported versions and fix notes in `SECURITY.md`.
- [ ] Publish a security advisory via GitHub Security Advisory.
- [ ] Sync the information across community channels (Discussions, Twitter/X, Zhihu, etc.).

---

## Historical Release Records

| Version | Release Date | Released By | Notes |
|------|----------|--------|------|
| 1.0.0 | 2026-06-19 | AutoShip Team | First stable release |
| 1.0.0-rc.1 | 2026-06-19 | AutoShip Team | First RC |
| 0.2.0-beta.1 | 2026-06-18 | AutoShip Team | Beta preview |
| 0.1.0 | 2026-06-18 | AutoShip Team | Initial version |
