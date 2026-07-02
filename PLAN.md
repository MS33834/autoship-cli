# AutoShip-CLI Roadmap

> **Status**: P1–P3 + P4-1 shipped (see [`FEATURES.md`](./FEATURES.md) and
> [`CHANGELOG.md`](./CHANGELOG.md)). Active work: **P4-2 → P4-6**, then the
> forward-looking **P5** expansion.
>
> **Living document**: every checkbox update is committed and mirrored to both
> remotes (GitHub `MS33834/autoship-cli` + GitCode `badhope/autoship-cli`) so
> progress is always visible. See _How to update this file_ below.

---

## How to use this roadmap

- Checkboxes use `- [ ]` (pending) / `- [x]` (done). Update them in the same
  commit as the work they describe.
- Every phase lists an **Owner role**, **Acceptance criteria**, and
  **Related files**. Do not mark a box done unless the acceptance criteria are
  met and the quality gate passes locally:
  ```bash
  uv run ruff check src tests dogfood benchmarks
  uv run ruff format --check src tests dogfood benchmarks
  uv run pyright
  uv run pytest -q
  uv run bandit -r src -ll
  uv run pip-audit --desc
  ```
- After committing, push to **both** remotes so the roadmap stays in sync:
  ```bash
  git push origin main && git push gitcode main
  ```
  (or run `scripts/sync.sh` if present).
- When a phase completes, add a one-line entry to `CHANGELOG.md` under
  `## [Unreleased]` and reference the phase ID.

---

## Team ownership

| Squad | Scope | Current phase |
|-------|-------|---------------|
| **Release / Integration** | versioning, changelog, automated release, packaging | P4-1 ✅, P4-3, P4-4 |
| **Docs / UX** | public docs site, tutorials, i18n, demos | P4-2, P4-6 |
| **Ecosystem / Plugins** | community plugins, review SOP, verified publishers | P4-3 |
| **Performance / Test** | scale tests, regression, stability | P4-4 |
| **Security / Compliance** | third-party audit, pentest, advisories | P4-5 |
| **Marketing / Ops** | launch announcement, README, social, feedback loop | P4-6 |
| **Platform / Forward** | GUI/TUI, IDE integration, multi-language, enterprise | P5 |

---

## Prior art (shipped foundation)

These are the completed milestones that everything below builds on. Details
live in `FEATURES.md`; only the phase IDs are mirrored here for continuity.

- [x] **P1-1** Registry index signature / integrity verification
- [x] **P1-2** Plugin install / update sha256 + signature verification
- [x] **P1-3** Audit log redaction strategy (keys + value patterns + unknown fields)
- [x] **P1-4** `commit` EDITOR allowlist validation
- [x] **P1-5** `verify` failure log redaction + `0o600` permissions
- [x] **P2-1** File permission tightening (`0o600`/`0o700`) across audit/registry/plugin state
- [x] **P2-2** `fix` file-path + extension allowlist
- [x] **P2-3** ToolVerifier PATH pollution protection (wired through commit/upload/verify/fix)
- [x] **P2-4** `docker_ship` `build_args` key + value validation
- [x] **P2-5** `ConfigCenter` environment-variable override allowlist
- [x] **P2-6** SIEM forwarding failure circuit-breaker + alert
- [x] **P2-7** Telemetry endpoint HTTPS validation
- [x] **P2-8** Model gateway error redaction across all 7 providers
- [x] **P3-1** Real AI backend integration (Ollama + LM Studio) + prompt path redaction
- [x] **P3-2** Real PyPI / Docker upload integration with local registry tests
- [x] **P3-3** Wheel / sdist distribution verification + `autoship-sdk` dependency hygiene
- [x] **P3-4** Full per-command reference docs (zh/en/ja)
- [x] **P3-5** GitHub Actions CI pipeline (ci/nightly/release/benchmark + TestPyPI)
- [x] **P3-6** Error messages + UX polish (i18n, next-step suggestions, UX tests)
- [x] **P3-7** Telemetry & privacy compliance (opt-in, PII filter, retention, docs)
- [x] **P3-8** Plugin store & publishing SOP (schema v2, audit_status, `typecheck` plugin)
- [x] **P4-1** Version management & release flow (SemVer, auto `CHANGELOG.md`, release checklist)

> A full back-rotation audit of every item above was performed: all gaps found
> (ToolVerifier wiring, prompt path leakage, locale parity, docs sync) have
> been fixed and the gate is green (670 passed / 17 skipped, 87.88% coverage,
> ruff + pyright + bandit clean).

---

## P4 — Release readiness (active)

Goal: turn "usable" into "a trustworthy product" — stable cadence, public
docs, verifiable security, active plugin ecosystem, and a real launch.

### P4-2 Public documentation site

- **Owner**: Docs / UX（主），Release/Integration（CI），Security/Compliance（审查），Performance/Test（构建验证）
- **Acceptance**: a deployed, searchable, trilingual docs site with quickstart,
  command reference, plugin dev guide, model config, privacy, FAQ; CI auto-
  deploys on push to `main`.
- **Related files**: `docs/`, `docs/en/`, `docs/ja/`, `mkdocs.yml`,
  `.github/workflows/website.yml`, `website/`, `README*.md`.
- **Detailed plan**: see [`docs/reviews/p4-2-public-docs-site-plan.md`](./docs/reviews/p4-2-public-docs-site-plan.md)
  for the full sub-task checklist (9 sections, ~50 items) including the
  Dependabot PR triage, mkdocs strict CI gate, trilingual quickstart/models/
  plugin tutorial, asciinema demo, and multi-role review.

> Reality check: `website.yml` already auto-deploys to GitHub Pages on `main`
> push (CI green); `mkdocs.yml` already has i18n zh/en/ja + mike configured.
> P4-2 work is therefore **content + strict-gate + demo + Dep cleanup**, not
> greenfield CI setup.

Tasks (mirrored from the detailed plan; check both here and the plan file):

- [x] **0** Triage 5 open Dependabot PRs (#38–#42): unified upgrade on one branch, verify CI, merge, close PRs
- [x] **1** `mkdocs build --strict` passes with 0 warning; add strict gate to `ci.yml` (independent docs job) + `website.yml` deploy
- [x] **2** Trilingual Quickstart + Why AutoShip + Troubleshooting + Known Issues + FAQ update + front matter titles complete (zh/en/ja)
- [x] **3** `docs/demo.md` recording script aligned + redaction showcase + recording env spec; landing page hero + CTA on 3 locale index pages; cross-locale link fixes (4 links in website/*.html)
- [x] **4** README ↔ docs site cross-links; edit-this-page links verified; CONTRIBUTING.md health-check section added
- [x] **5** Search CJK (en/ja lang) configured; mike versioning deferred (documented migration path)
- [x] **6** `website.yml` deploy with `--strict`; smoke-test checklist + `robots.txt` + SEO ready (deploy verification pending push)
- [x] **7** Multi-role review (architect/PM/dev-lead/security/test) executed pre-implementation; findings addressed in supplementary tasks
- [x] **8** Full gate green: ruff + pyright + mkdocs strict + i18n sync + command docs sync + docs secret scan + pytest (656 passed, 87.88% coverage)
- [x] **9** PLAN.md checkboxes flipped, CHANGELOG `[Unreleased]` updated, dual-remote sync pending commit

> **Note**: `docs/demo.cast` (asciinema recording) and screenshots/GIFs require
> human recording in a GUI environment — deferred. The demo script and
> recording environment spec are ready in `docs/demo.md`. New-user live test
> (task 7.7) also deferred to post-merge community feedback.

### P4-3 Community plugin collection & review

- **Owner**: Ecosystem / Plugins
- **Acceptance**: published submission template + review checklist; ≥5
  community/official plugins in the registry; documented verified-publisher
  flow.
- **Related files**: `docs/plugin-publishing.md`, `registry/plugins.json`,
  `registry/schema.json`, `registry-web/`, `.github/PULL_REQUEST_TEMPLATE.md`.

Tasks:

- [ ] Author plugin submission PR template (metadata, sha256, signature, permissions).
- [ ] Publish reviewer checklist (license, permissions, sandbox test, signature).
- [ ] Reach ≥5 reviewed plugins in `registry/plugins.json` (current: `docker-ship`, `security-scan`, `web-search`, `typecheck` — add at least one external contribution).
- [ ] Define and document the **verified publisher** criteria + badge.
- [ ] Add registry-web filter/sort by `trust_level` and `audit_status`.
- [ ] Add an automated `scripts/validate_plugin_entry.py` run in CI on registry PRs.
- [ ] Write a "publish your first plugin" blog post (zh + en).

### P4-4 Performance & scale testing

- **Owner**: Performance / Test
- **Acceptance**: baseline numbers on a 1000+ file project for `clean` /
  `verify` / `upload --dry-run`; concurrency safety proven; 24h soak shows no
  memory leak.
- **Related files**: `benchmarks/benchmark.py`, `dogfood/dogfood.py`,
  `src/autoship/core/metrics.py`, `src/autoship/core/audit_logger.py`.

Tasks:

- [ ] Build a 1000+ file fixture repo (or vendor a synthetic one) under `benchmarks/fixtures/`.
- [ ] Record baseline JSON for `clean`, `verify`, `upload --dry-run` on the fixture.
- [ ] Add a threaded concurrency test that drives `metrics` + `audit_logger` in parallel and asserts no race.
- [ ] Add a 24h soak harness (or CI nightly job) capturing RSS over time; assert growth < 10%.
- [ ] Refresh `benchmarks/results.json` baseline + add a regression threshold to `benchmark.yml`.
- [ ] Publish a `docs/performance.md` page with the methodology + numbers (zh/en/ja).

### P4-5 Security audit & penetration test

- **Owner**: Security / Compliance
- **Acceptance**: pass `pip-audit` + `bandit` + Dependabot/Renovate; one
  third-party or internal red-team pentest pass; all H/M findings fixed and
  advisory published.
- **Related files**: `pyproject.toml`, `.github/workflows/nightly.yml`,
  `docs/security-audit.md`, `docs/security.md`.

Tasks:

- [ ] Enable Dependabot (or Renovate) config for Python + GitHub Actions.
- [ ] Add `pip-audit` + `bandit` as required status checks (already in nightly; gate PRs too).
- [ ] Commission an internal/external pentest scoped to: plugin install path, ToolVerifier bypass, prompt injection via `verify --fix`, upload credential handling.
- [ ] Remediate every H/M finding; record in `docs/security-audit.md`.
- [ ] Define a security advisory workflow (GitHub Security Advisories + CVE assignment).
- [ ] Publish a `SECURITY.md` disclosure policy (draft exists as `docs/security.md` — promote to root).

### P4-6 Launch & marketing

- **Owner**: Marketing / Ops
- **Acceptance**: README with badges/screenshots/asciinema; launch blog in
  zh+en; social posts on Twitter/Juejin/Zhihu; a feedback channel that feeds
  the next iteration.
- **Related files**: `README.md`, `README.zh.md`, `README.ja.md`, `website/`,
  `docs/announcement.md`.

Tasks:

- [ ] Polish README badges (CI, coverage, PyPI, license, docs, downloads).
- [ ] Embed `docs/demo.cast` (asciinema) in all three READMEs.
- [ ] Add a "Why AutoShip" section with the local-first pitch + comparison table.
- [ ] Write launch blog post (English on dev.to/Medium, Chinese on Juejin/Zhihu).
- [ ] Prepare social posts: Twitter (EN), Juejin + Zhihu (ZH), Qiita (JA).
- [ ] Open a GitHub Discussions category for Q&A + plugin showcase.
- [ ] Collect first-week feedback into a triaged issue batch for the next iteration.

---

## P5 — Forward expansion (post-1.0)

Stretch goals that extend AutoShip beyond a CLI into a fuller delivery
platform. Each is intentionally coarse-grained; promote to its own task list
when scheduled.

### P5-1 TUI / optional GUI

- [ ] Prototype a `textual`-based TUI (`autoship ui`) wrapping the CLI.
- [ ] Optional: VS Code extension reusing the CLI as backend.

### P5-2 Team collaboration

- [ ] Shared `.autoship.team.toml` profiles + signed config distribution.
- [ ] Centralized audit/telemetry sink for teams (self-hosted, opt-in).

### P5-3 Optional cloud backends

- [ ] Self-hosted model relay that preserves the local-first promise (proxy only).
- [ ] Documented data-flow guarantees so users can audit what leaves the machine.

### P5-4 Multi-language project support

- [ ] First-class clean/verify rules for Go, Rust, Node, Java (build artifacts, test dirs).
- [ ] Language-aware plugin packs (e.g. `go-ship`, `rust-ship`).

### P5-5 IDE integration

- [ ] Language Server Protocol shim exposing `verify` diagnostics.
- [ ] Run-on-save hooks for `clean` + `verify`.

### P5-6 Enterprise edition

- [ ] SSO / SCIM provisioning, role-based config.
- [ ] Compliance export (audit log → SIEM-ready bundles, SOC2 evidence).
- [ ] Air-gapped install path (offline plugin registry mirror).

---

## Appendix

### Quality gate (run before every checkbox flip)

```bash
uv run ruff check src tests dogfood benchmarks
uv run ruff format --check src tests dogfood benchmarks
uv run pyright
uv run pytest -q
uv run bandit -r src -ll
uv run pip-audit --desc
uv run mkdocs build --strict --site-dir /tmp/mkdocs-build
```

Target: 0 ruff errors, 0 pyright errors, all tests green, coverage ≥85%,
bandit clean, no known CVEs, mkdocs strict 0 warning.

### Remote repository health check (mandatory before & after every phase)

> Documented in [`CONTRIBUTING.md`](./CONTRIBUTING.md) § "远程仓库健康检查".
> Every developer MUST run this check before starting work, before each
> commit, and after each push.

1. **PRs**: any open PR (including Dependabot)? CI green? conflicts?
2. **Issues**: any untriaged issue? bug labeled but unfixed?
3. **Branches**: stale feature branches? GitCode mirror in sync with GitHub?
4. **CI**: main branch all workflows green (CI/E2E/Nightly/Deploy Website)?
5. **Security**: Dependabot advisories? `pip-audit` clean?

Never stack new commits on red CI. Never leave GitCode mirror behind.
Record the check result in the commit message or review doc.

### Dual-remote sync

```bash
git push origin main      # GitHub: MS33834/autoship-cli
git push gitcode main     # GitCode: badhope/autoship-cli
```

Both remotes are configured without embedded tokens; credentials are read
from `~/.git-credentials`. Never commit tokens to the repository.

### Changelog hygiene

- Every completed phase adds an entry under `## [Unreleased]` in
  `CHANGELOG.md` (root, auto-generated on release) and `docs/changelog.md`
  (trilingual narrative).
- Use Keep a Changelog categories: `Added` / `Changed` / `Fixed` / `Security`.
- On release, `scripts/release_changelog.py` folds `Unreleased` into a tagged
  section automatically.
