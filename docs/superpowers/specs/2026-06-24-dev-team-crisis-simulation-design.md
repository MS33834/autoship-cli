# DevTeam Crisis Simulation Suite — Design Spec

## Goal
Simulate a real engineering team using AutoShip-CLI under pressure: tight deadlines,
mid-stream requirement changes, conflicting security policies, and messy legacy code.
The suite will run three new phases (D1/D2/D3), record every CLI invocation, and feed
discovered issues back into the CLI implementation.

## Scope

### D1 — Emergency Internal Plugin Delivery

**Personas**
- **Alice** — senior backend engineer, drives the design
- **Bob** — junior full-stack, makes environment mistakes
- **Boss** — strict CTO who changes requirements mid-flight

**Scenario**
The team must deliver `autoship-commit-policy`, a plugin that enforces company
commit-message rules, within a simulated 2-hour deadline.

**Required plugin capabilities**
1. Reject commits whose message does not match `type(scope): subject`
2. Block WIP/TODO/XXX commits when `--block-wip-commits` is enabled
3. Emit audit log entries via the existing `autoship.core.audit_logger`
4. Provide i18n messages for EN/ZH/JA
5. Register an entry point under `autoship.plugins`

**Injected problems**
- Bob runs `autoship doctor` on Python 3.9; the project requires `>=3.10`
- The plugin writes audit logs; first sandbox run fails because filesystem is read-only
- Boss adds `--block-wip-commits` after the first test run
- Initial unit-test coverage is below the 85 % gate
- Bandit flags `subprocess.run` in the plugin; we must decide whether it is a false positive

**Success criteria**
- `autoship plugin install <local-dir>` succeeds
- `autoship verify pytest` passes with ≥85 % coverage
- `autoship commit -m "feat: add policy"` succeeds
- `autoship commit -m "WIP foo"` fails with a clear i18n message
- `autoship plugin upload --registry local` succeeds

### D2 — Pre-Launch Repo Rescue

**Personas**
- **Carol** — staff engineer, methodical
- **Dave** — senior engineer, takes shortcuts
- **Evan** — junior engineer, panics and misconfigures

**Scenario**
A third-party integration project must ship in the morning but the repository is in
bad shape. Each persona attempts to rescue it with a different workflow.

**Repository state**
- No `.autoship.toml`
- `ruff` and `black` missing from the environment
- Hard-coded `AWS_SECRET_ACCESS_KEY` in `src/acme/config.py`
- `tests/test_core.py` has a failing assertion
- A wheel dependency has a mismatched SHA-256 in `.autoship.lock`

**Persona workflows**
1. **Carol** — `doctor` → `init --yes` → manual secret removal → `fix` → `verify pytest`
2. **Dave** — `fix --yes` directly, expecting AutoShip to handle everything
3. **Evan** — writes an invalid `.autoship.toml` and then runs `doctor`

**Success criteria**
- Carol's workflow ends with a passing `verify` and a clean `commit`
- Dave's workflow exposes the limits of `fix` and produces a useful error
- Evan's invalid config is rejected with a clear suggestion (`Run autoship init`)
- Security scan flags the hard-coded secret

### D3 — Multi-Developer Policy Conflict

**Personas**
- **Frank** — DevOps, prioritizes velocity
- **Grace** — security engineer, prioritizes lockdown

**Scenario**
Two developers apply conflicting trust/sandbox policies to the same project.

**Conflicts**
- Frank installs a community plugin with `--no-sandbox`
- Grace sets `sandbox.required = true` in `.autoship.team.toml`
- Frank sets `verify.allowed_commands = ["pytest", "python"]` in user config
- Grace adds `verify.allowed_commands = ["pytest", "bandit"]` in team config
- Both push changes; the next `autoship verify` must resolve precedence clearly

**Success criteria**
- CLI reports the policy conflict instead of silently overriding
- Team config takes precedence over user config for `verify.allowed_commands`
- Installing an UNTRUSTED plugin with `--no-sandbox` is hard-blocked
- The error message names the exact plugin and the conflicting setting

## Shared Infrastructure

Add `dogfood/dev_team_crisis/`:
- `runner.py` — reuse or extend `dogfood.real_world.runner` helpers
- `phase_d1.py`, `phase_d2.py`, `phase_d3.py` — one module per phase
- `run_all.py` — execute D1→D2→D3 and write Markdown/JSON reports
- `reports/` — generated artifacts (gitignored)

## Optimization Backlog (to be filled during execution)

Known areas to watch and possibly improve:
- Error messages when `doctor` sees an invalid config
- Sandbox failure messages that explain which capability is missing
- `fix` command behavior on repositories with mixed Python/Node code
- Plugin registry upload path for local/custom registries
- Precedence rules for team vs user config

## Definition of Done

1. D1, D2, D3 scenarios are implemented and runnable via `python dogfood/dev_team_crisis/run_all.py`
2. All scenarios pass, or every failure is documented as a discovered bug
3. Discovered bugs/fixes are applied to `src/autoship/...`
4. Full quality gate re-run passes: ruff, pyright, pytest, bandit, pip-audit
5. Changes are committed and pushed to GitHub and GitCode
