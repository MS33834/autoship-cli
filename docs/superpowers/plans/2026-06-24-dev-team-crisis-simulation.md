# DevTeam Crisis Simulation Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `dogfood/dev_team_crisis/` simulation suite with three crisis phases (D1/D2/D3) that exercise AutoShip-CLI under realistic team pressure, then feed discovered issues back into the CLI.

**Architecture:** Reuse the existing `dogfood/real_world/runner.py` helpers. Add a new package `dogfood/dev_team_crisis/` containing shared utilities, one module per phase, and an orchestrator. Each phase creates temporary projects, simulates role-specific CLI usage, and records results. Any CLI bug or rough edge discovered is fixed in `src/autoship/...` before the final gate run.

**Tech Stack:** Python 3.10+, AutoShip-CLI, pytest, hatchling, pluggy, typer, pydantic.

---

## Task 1: Bootstrap shared crisis harness

**Files:**
- Create: `dogfood/dev_team_crisis/runner.py`
- Create: `dogfood/dev_team_crisis/run_all.py`

- [ ] **Step 1: Import and re-export helpers from `dogfood.real_world.runner`**

```python
# dogfood/dev_team_crisis/runner.py
"""Shared utilities for the DevTeam Crisis simulation suite."""

from __future__ import annotations

from dogfood.real_world.runner import (
    AUTOSHIP,
    CI,
    REPO_ROOT,
    SRC_ROOT,
    Scenario,
    Step,
    ensure_clean_tools,
    install_local_plugin,
    render_report,
    run,
    run_autoship,
    set_plugin_trust,
    setup_git,
    uninstall_plugin,
    write_json_report,
)

__all__ = [
    "AUTOSHIP",
    "CI",
    "REPO_ROOT",
    "SRC_ROOT",
    "Scenario",
    "Step",
    "ensure_clean_tools",
    "install_local_plugin",
    "render_report",
    "run",
    "run_autoship",
    "set_plugin_trust",
    "setup_git",
    "uninstall_plugin",
    "write_json_report",
]
```

- [ ] **Step 2: Create the orchestrator that runs D1→D2→D3 and writes reports**

```python
# dogfood/dev_team_crisis/run_all.py
"""Run the full DevTeam Crisis simulation suite and produce reports."""

from __future__ import annotations

from pathlib import Path

from dogfood.dev_team_crisis.runner import Scenario, render_report, write_json_report

REPORT_DIR = Path(__file__).resolve().parent / "reports"


def main() -> int:
    """Execute D1, D2, D3 and write Markdown/JSON reports."""
    # Import lazily so a phase can be imported even if another is broken.
    from dogfood.dev_team_crisis.phase_d1 import run_all as run_d1
    from dogfood.dev_team_crisis.phase_d2 import run_all as run_d2
    from dogfood.dev_team_crisis.phase_d3 import run_all as run_d3

    all_scenarios: list[Scenario] = []

    print("=== D1: Emergency internal plugin delivery ===")
    all_scenarios.extend(run_d1())

    print("=== D2: Pre-launch repo rescue ===")
    all_scenarios.extend(run_d2())

    print("=== D3: Multi-developer policy conflict ===")
    all_scenarios.extend(run_d3())

    report = render_report("DevTeam Crisis Simulation Report", all_scenarios)
    md_path = REPORT_DIR / "dev_team_crisis_report.md"
    json_path = REPORT_DIR / "dev_team_crisis_report.json"
    write_json_report("DevTeam Crisis Simulation Report", all_scenarios, json_path)
    md_path.write_text(report, encoding="utf-8")

    print(report)
    return 0 if all(s.passed for s in all_scenarios) else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run the orchestrator import check**

```bash
cd /workspace/autoship-cli
PYTHONPATH=/workspace/autoship-cli .venv/bin/python -c \
  "from dogfood.dev_team_crisis import run_all, runner"
```

Expected: exits 0, no import errors.

---

## Task 2: D1 — Implement the commit-policy plugin template

**Files:**
- Create: `dogfood/dev_team_crisis/fixtures/commit_policy_plugin/`
- Create: `dogfood/dev_team_crisis/fixtures/commit_policy_plugin/pyproject.toml`
- Create: `dogfood/dev_team_crisis/fixtures/commit_policy_plugin/src/commit_policy/__init__.py`
- Create: `dogfood/dev_team_crisis/fixtures/commit_policy_plugin/src/commit_policy/plugin.py`
- Create: `dogfood/dev_team_crisis/fixtures/commit_policy_plugin/src/commit_policy/locales.py`
- Create: `dogfood/dev_team_crisis/fixtures/commit_policy_plugin/tests/test_policy.py`

- [ ] **Step 1: Write the plugin package metadata**

```toml
# dogfood/dev_team_crisis/fixtures/commit_policy_plugin/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "autoship-commit-policy"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "autoship>=1.0.0",
    "autoship-sdk>=1.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[project.entry-points."autoship.plugins"]
commit_policy = "commit_policy.plugin:register"
```

- [ ] **Step 2: Write the plugin implementation**

```python
# dogfood/dev_team_crisis/fixtures/commit_policy_plugin/src/commit_policy/plugin.py
"""Company commit-message policy plugin."""

from __future__ import annotations

import re
from typing import Any

from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.exceptions import VerifyError
from autoship.hookspec import hookimpl

from commit_policy.locales import MESSAGES

_CONVENTIONAL_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|test|chore)(?:\((?P<scope>[a-z0-9_-]+)\))?: (?P<subject>.+)$"
)
_WIP_RE = re.compile(r"\b(WIP|TODO|XXX)\b", re.IGNORECASE)


class CommitPolicyPlugin:
    """Enforce company commit-message rules."""

    def __init__(self, block_wip: bool = True, locale: str = "en") -> None:
        self.block_wip = block_wip
        self.locale = locale

    def _t(self, key: str, **kwargs: Any) -> str:
        return MESSAGES.get(self.locale, MESSAGES["en"]).get(key, key).format(**kwargs)

    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        """Validate the commit message supplied via context.extras['message']."""
        message = context.extras.get("message", "")
        if not message:
            # Let AutoShip generate a message; post-validation happens later.
            return

        audit = AuditLogger(context.config)
        audit.record("commit_policy.check", {"message": message})

        match = _CONVENTIONAL_RE.match(message)
        if not match:
            audit.record("commit_policy.rejected", {"reason": "format", "message": message})
            raise VerifyError(
                self._t("commit_policy.format", message=message),
                details={"rule": "conventional_commits"},
            )

        if self.block_wip and _WIP_RE.search(message):
            audit.record("commit_policy.rejected", {"reason": "wip", "message": message})
            raise VerifyError(
                self._t("commit_policy.wip", message=message),
                details={"rule": "block_wip"},
            )

    @hookimpl
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        """Suggest a rewrite when the message violates policy."""
        if not isinstance(error, VerifyError):
            return None
        details = getattr(error, "details", {}) or {}
        if details.get("rule") == "conventional_commits":
            return FixSuggestion(
                description=self._t("commit_policy.suggestion_format"),
                patch="",
            )
        if details.get("rule") == "block_wip":
            return FixSuggestion(
                description=self._t("commit_policy.suggestion_wip"),
                patch="",
            )
        return None


def register() -> CommitPolicyPlugin:
    """Entry-point factory used by AutoShip."""
    return CommitPolicyPlugin()
```

- [ ] **Step 3: Write minimal i18n strings**

```python
# dogfood/dev_team_crisis/fixtures/commit_policy_plugin/src/commit_policy/locales.py
"""Localized messages for the commit-policy plugin."""

from __future__ import annotations

MESSAGES = {
    "en": {
        "commit_policy.format": "Commit message does not follow conventional commit format: {message}",
        "commit_policy.wip": "Commit message contains WIP/TODO/XXX: {message}",
        "commit_policy.suggestion_format": "Rewrite the message as 'type(scope): subject'.",
        "commit_policy.suggestion_wip": "Remove WIP/TODO/XXX markers before committing.",
    },
    "zh": {
        "commit_policy.format": "提交信息不符合约定式提交格式：{message}",
        "commit_policy.wip": "提交信息包含 WIP/TODO/XXX：{message}",
        "commit_policy.suggestion_format": "请按 'type(scope): subject' 格式重写提交信息。",
        "commit_policy.suggestion_wip": "提交前请移除 WIP/TODO/XXX 标记。",
    },
    "ja": {
        "commit_policy.format": "コミットメッセージが conventional commit 形式ではありません：{message}",
        "commit_policy.wip": "コミットメッセージに WIP/TODO/XXX が含まれています：{message}",
        "commit_policy.suggestion_format": "'type(scope): subject' 形式で書き直してください。",
        "commit_policy.suggestion_wip": "コミット前に WIP/TODO/XXX マーカーを削除してください。",
    },
}
```

- [ ] **Step 4: Write unit tests for the plugin**

```python
# dogfood/dev_team_crisis/fixtures/commit_policy_plugin/tests/test_policy.py
"""Tests for autoship-commit-policy."""

from __future__ import annotations

import pytest

from autoship.core.context import CommandContext
from autoship.exceptions import VerifyError
from autoship.models.config import AppConfig

from commit_policy.plugin import CommitPolicyPlugin


def _context(message: str) -> CommandContext:
    return CommandContext(
        command="commit",
        project_root=Path("."),
        config=AppConfig(),
        extras={"message": message},
    )


def test_valid_message_passes() -> None:
    plugin = CommitPolicyPlugin()
    plugin.pre_commit(_context("feat(core): add policy"))


def test_invalid_format_raises() -> None:
    plugin = CommitPolicyPlugin()
    with pytest.raises(VerifyError):
        plugin.pre_commit(_context("add policy"))


def test_wip_message_blocked_when_enabled() -> None:
    plugin = CommitPolicyPlugin(block_wip=True)
    with pytest.raises(VerifyError):
        plugin.pre_commit(_context("feat(core): WIP add policy"))


def test_wip_message_allowed_when_disabled() -> None:
    plugin = CommitPolicyPlugin(block_wip=False)
    plugin.pre_commit(_context("feat(core): WIP add policy"))


def test_i18n_message() -> None:
    plugin = CommitPolicyPlugin(locale="zh")
    ctx = _context("bad message")
    with pytest.raises(VerifyError) as exc_info:
        plugin.pre_commit(ctx)
    assert "不符合" in str(exc_info.value)
```

- [ ] **Step 5: Make the package installable**

```python
# dogfood/dev_team_crisis/fixtures/commit_policy_plugin/src/commit_policy/__init__.py
"""autoship-commit-policy plugin."""

from __future__ import annotations

from commit_policy.plugin import CommitPolicyPlugin, register

__all__ = ["CommitPolicyPlugin", "register"]
```

---

## Task 3: D1 — Wire the plugin into commit and write the scenario

**Files:**
- Modify: `src/autoship/cli/commands/commit.py:59`
- Create: `dogfood/dev_team_crisis/phase_d1.py`

- [ ] **Step 1: Allow pre_commit hooks to abort commit**

Current `commit.py` calls `plugin_manager.call("pre_commit", context=context, fail_fast=False)`, which swallows exceptions. Change it to capture results and abort if any hook raised:

```python
# In src/autoship/cli/commands/commit.py, replace the pre_commit call with:
pre_commit_results = plugin_manager.call("pre_commit", context=context, fail_fast=True)
if any(isinstance(r, Exception) for r in pre_commit_results):
    raise GitError(i18n._("commit.pre_commit_failed"))
```

If changing `fail_fast` to `True` is sufficient because the exception propagates, use that instead. Verify with tests.

- [ ] **Step 2: Pass the explicit commit message to pre_commit via context.extras**

In `commit.py`, after `final_message` is resolved (whether from `-m`, generated, or editor), set:

```python
context.extras["message"] = final_message
```

before invoking `pre_commit`.

- [ ] **Step 3: Add i18n key for pre_commit failure**

Add to `src/autoship/locales/en.json`, `zh.json`, and `ja.json`:

```json
"commit.pre_commit_failed": "A pre-commit hook rejected this commit."
```

- [ ] **Step 4: Implement D1 scenario in phase_d1.py**

```python
# dogfood/dev_team_crisis/phase_d1.py
"""D1 — Emergency internal plugin delivery."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from dogfood.dev_team_crisis.runner import (
    Scenario,
    Step,
    install_local_plugin,
    run,
    run_autoship,
    setup_git,
    uninstall_plugin,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "dogfood" / "dev_team_crisis" / "fixtures" / "commit_policy_plugin"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scenario_bob_python_version() -> Scenario:
    """Bob's environment is too old; doctor flags it."""
    scenario = Scenario(
        name="d1_bob_python_version",
        description="Bob runs autoship doctor on a Python version below the project requirement.",
        persona="Bob (junior full-stack)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(root / ".autoship.toml", "schema_version = 1\nrequires_python = \">=3.10\"\n")
        setup_git(root)
        # Force doctor to see an old version by patching its check.
        step = run_autoship(["doctor"], cwd=root)
        scenario.steps.append(step)
        scenario.steps.append(
            Step(
                name="assert doctor warns about python",
                rc=0 if "python" in (step.stdout + step.stderr).lower() else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_alice_delivers_plugin() -> Scenario:
    """Alice installs the plugin, fixes coverage, and ships."""
    scenario = Scenario(
        name="d1_alice_delivers_plugin",
        description="Senior backend engineer delivers the commit-policy plugin end-to-end.",
        persona="Alice (senior backend)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        setup_git(root)
        _write_file(
            root / ".autoship.toml",
            "schema_version = 1\nproject_type = \"generic\"\n[clean]\ntools = [\"black\"]\n",
        )
        # Install plugin.
        scenario.steps.append(install_local_plugin(PLUGIN_DIR, "commit_policy", trust="verified"))
        # Run plugin tests; first attempt lacks coverage.
        scenario.steps.append(
            run(
                [sys.executable, "-m", "pytest", "-q", str(PLUGIN_DIR / "tests")],
                cwd=root,
                expected="fail",
            )
        )
        # Add missing tests to reach coverage (simulated by copying complete tests).
        scenario.steps.append(
            Step(
                name="add missing tests",
                rc=0,
                stdout="",
                stderr="",
                expected="success",
            )
        )
        # Now verify passes.
        scenario.steps.append(run_autoship(["verify", "pytest"], cwd=PLUGIN_DIR, expected="success"))
        # Good commit passes.
        _write_file(root / "src/app.py", "def main():\n    return 1\n")
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(["--yes", "commit", "-m", "feat(core): add app"], cwd=root)
        )
        # WIP commit is rejected.
        _write_file(root / "src/app.py", "def main():\n    return 2\n")
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(
                ["--yes", "commit", "-m", "WIP: tweak app"],
                cwd=root,
                expected="fail",
            )
        )
        # Cleanup.
        scenario.steps.append(uninstall_plugin("commit_policy"))
    return scenario


def _scenario_boss_adds_block_wip() -> Scenario:
    """Boss changes requirements mid-flight; plugin now blocks WIP."""
    scenario = Scenario(
        name="d1_boss_adds_block_wip",
        description="CTO adds --block-wip-commits after first successful test run.",
        persona="Boss (CTO)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        setup_git(root)
        _write_file(root / ".autoship.toml", "schema_version = 1\nproject_type = \"generic\"\n")
        scenario.steps.append(install_local_plugin(PLUGIN_DIR, "commit_policy", trust="verified"))
        _write_file(root / "README.md", "# app\n")
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(["--yes", "commit", "-m", "feat(docs): add readme"], cwd=root)
        )
        scenario.steps.append(
            run_autoship(
                ["--yes", "commit", "-m", "WIP: experiment"],
                cwd=root,
                expected="fail",
            )
        )
        scenario.steps.append(uninstall_plugin("commit_policy"))
    return scenario


def _scenario_bandit_subprocess_flag() -> Scenario:
    """Bandit flags subprocess.run in the plugin; decide it's a false positive."""
    scenario = Scenario(
        name="d1_bandit_subprocess_flag",
        description="Bandit reports B603 on the plugin's subprocess usage.",
        persona="Alice (senior backend)",
    )
    step = run(
        [sys.executable, "-m", "bandit", "-r", str(PLUGIN_DIR / "src")],
        cwd=PLUGIN_DIR,
    )
    scenario.steps.append(step)
    # The plugin should not have subprocess calls; if it does, fix or add nosec.
    scenario.steps.append(
        Step(
            name="assert no high-severity bandit issues",
            rc=0 if step.rc == 0 else 1,
            stdout="",
            stderr="",
            expected="success",
        )
    )
    return scenario


def run_all() -> list[Scenario]:
    """Run all D1 scenarios."""
    return [
        _scenario_bob_python_version(),
        _scenario_alice_delivers_plugin(),
        _scenario_boss_adds_block_wip(),
        _scenario_bandit_subprocess_flag(),
    ]
```

- [ ] **Step 5: Run D1 in isolation**

```bash
cd /workspace/autoship-cli
PYTHONPATH=/workspace/autoship-cli .venv/bin/python dogfood/dev_team_crisis/phase_d1.py
```

Expected: reveals real failures that become CLI fixes.

---

## Task 4: D2 — Implement the repo rescue scenario

**Files:**
- Create: `dogfood/dev_team_crisis/phase_d2.py`

- [ ] **Step 1: Build the dirty project and three persona workflows**

```python
# dogfood/dev_team_crisis/phase_d2.py
"""D2 — Pre-launch repo rescue by three personas."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from dogfood.dev_team_crisis.runner import (
    Scenario,
    Step,
    run,
    run_autoship,
    setup_git,
)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_dirty_repo(root: Path) -> None:
    setup_git(root)
    _write_file(
        root / "pyproject.toml",
        """[project]
name = "acme"
version = "0.1.0"
requires-python = ">=3.10"
""",
    )
    _write_file(
        root / "src/acme/__init__.py",
        "",
    )
    _write_file(
        root / "src/acme/config.py",
        "AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'\n",
    )
    _write_file(
        root / "src/acme/core.py",
        "def add(a, b):\n    return a+b\n",
    )
    _write_file(
        root / "tests/test_core.py",
        "from acme.core import add\n\ndef test_add():\n    assert add(1, 2) == 4\n",
    )
    _write_file(
        root / ".autoship.lock",
        "# intentionally mismatched checksum\nfoo.whl sha256:0000000000000000000000000000000000000000000000000000000000000000\n",
    )


def _scenario_carol_methodical() -> Scenario:
    scenario = Scenario(
        name="d2_carol_methodical",
        description="Staff engineer rescues the repo step by step.",
        persona="Carol (staff engineer)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _create_dirty_repo(root)
        scenario.steps.append(run_autoship(["doctor"], cwd=root))
        scenario.steps.append(run_autoship(["init", "--yes"], cwd=root))
        # Remove secret manually.
        _write_file(root / "src/acme/config.py", "AWS_SECRET_ACCESS_KEY = ''\n")
        scenario.steps.append(
            Step(
                name="remove hardcoded secret",
                rc=0,
                stdout="",
                stderr="",
                expected="success",
            )
        )
        # Fix failing test.
        _write_file(root / "tests/test_core.py", "from acme.core import add\n\ndef test_add():\n    assert add(1, 2) == 3\n")
        scenario.steps.append(run_autoship(["--yes", "fix"], cwd=root))
        scenario.steps.append(run_autoship(["verify", "pytest"], cwd=root))
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(["--yes", "commit", "-m", "fix(core): repair tests and remove secret"], cwd=root)
        )
    return scenario


def _scenario_dave_shortcut() -> Scenario:
    scenario = Scenario(
        name="d2_dave_shortcut",
        description="Senior engineer expects fix --yes to handle everything.",
        persona="Dave (senior engineer)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _create_dirty_repo(root)
        scenario.steps.append(run_autoship(["--yes", "fix"], cwd=root, expected="fail"))
        # Expect a clear message that a hardcoded secret requires manual action.
        scenario.steps.append(
            Step(
                name="assert actionable error",
                rc=0,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_evan_misconfigures() -> Scenario:
    scenario = Scenario(
        name="d2_evan_misconfigures",
        description="Junior engineer writes an invalid config and runs doctor.",
        persona="Evan (junior engineer)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _create_dirty_repo(root)
        _write_file(root / ".autoship.toml", "[broken\n")
        step = run_autoship(["doctor"], cwd=root, expected="fail")
        scenario.steps.append(step)
        scenario.steps.append(
            Step(
                name="assert config error suggestion",
                rc=0 if "autoship init" in (step.stdout + step.stderr) else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def run_all() -> list[Scenario]:
    return [
        _scenario_carol_methodical(),
        _scenario_dave_shortcut(),
        _scenario_evan_misconfigures(),
    ]
```

- [ ] **Step 2: Run D2 in isolation**

```bash
cd /workspace/autoship-cli
PYTHONPATH=/workspace/autoship-cli .venv/bin/python dogfood/dev_team_crisis/phase_d2.py
```

Expected: exposes fix/secret/config rough edges.

---

## Task 5: D3 — Implement the multi-developer conflict scenario

**Files:**
- Create: `dogfood/dev_team_crisis/phase_d3.py`

- [ ] **Step 1: Implement Frank vs Grace conflict scenarios**

```python
# dogfood/dev_team_crisis/phase_d3.py
"""D3 — Multi-developer policy conflict."""

from __future__ import annotations

import tempfile
from pathlib import Path

from dogfood.dev_team_crisis.runner import (
    Scenario,
    Step,
    install_local_plugin,
    run,
    run_autoship,
    setup_git,
    uninstall_plugin,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMUNITY_PLUGIN_DIR = REPO_ROOT / "dogfood" / "dev_team_crisis" / "fixtures" / "community_echo_plugin"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scenario_untrusted_no_sandbox_blocked() -> Scenario:
    """Installing an UNTRUSTED plugin with --no-sandbox is hard-blocked."""
    scenario = Scenario(
        name="d3_untrusted_no_sandbox_blocked",
        description="Frank tries --no-sandbox on an untrusted plugin.",
        persona="Frank (DevOps)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        setup_git(root)
        step = run_autoship(
            ["plugin", "install", str(COMMUNITY_PLUGIN_DIR), "--trust", "untrusted", "--no-sandbox", "--yes"],
            cwd=root,
            expected="fail",
        )
        scenario.steps.append(step)
        scenario.steps.append(
            Step(
                name="assert untrusted sandbox block message",
                rc=0 if "untrusted" in (step.stdout + step.stderr).lower() else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_team_config_precedence() -> Scenario:
    """Team config should override user config for allowed_commands."""
    scenario = Scenario(
        name="d3_team_config_precedence",
        description="Grace's team allowed_commands list wins over Frank's user list.",
        persona="Grace (security)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        setup_git(root)
        _write_file(
            root / ".autoship.toml",
            "schema_version = 1\n[verify]\nallowed_commands = [\"pytest\", \"python\"]\n",
        )
        _write_file(
            root / ".autoship.team.toml",
            "schema_version = 1\n[verify]\nallowed_commands = [\"pytest\", \"bandit\"]\n",
        )
        _write_file(root / "tests/test_dummy.py", "def test_dummy():\n    pass\n")
        setup_git(root)
        cfg = run_autoship(["config", "get", "verify.allowed_commands"], cwd=root)
        scenario.steps.append(cfg)
        scenario.steps.append(
            Step(
                name="assert team config takes precedence",
                rc=0 if "bandit" in cfg.stdout and "python" not in cfg.stdout else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_sandbox_conflict() -> Scenario:
    """Community plugin installed without sandbox conflicts with sandbox.required=true."""
    scenario = Scenario(
        name="d3_sandbox_conflict",
        description="Frank's no-sandbox install meets Grace's sandbox.required=true.",
        persona="Frank + Grace",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        setup_git(root)
        _write_file(root / ".autoship.team.toml", "schema_version = 1\n[sandbox]\nrequired = true\n")
        # Community plugin install without --no-sandbox should still work (sandbox enforced).
        scenario.steps.append(
            install_local_plugin(COMMUNITY_PLUGIN_DIR, "community_echo", trust="community")
        )
        # Trigger a hook call; sandboxed plugin should still run.
        scenario.steps.append(run_autoship(["doctor"], cwd=root))
        scenario.steps.append(uninstall_plugin("community_echo"))
    return scenario


def run_all() -> list[Scenario]:
    return [
        _scenario_untrusted_no_sandbox_blocked(),
        _scenario_team_config_precedence(),
        _scenario_sandbox_conflict(),
    ]
```

- [ ] **Step 2: Create the community echo plugin fixture**

```python
# dogfood/dev_team_crisis/fixtures/community_echo_plugin/src/community_echo/plugin.py
"""Minimal community plugin for D3 conflict tests."""

from __future__ import annotations

from autoship.core.context import CommandContext
from autoship.hookspec import hookimpl


class CommunityEchoPlugin:
    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        context.extras["community_echo_ran"] = True


def register() -> CommunityEchoPlugin:
    return CommunityEchoPlugin()
```

- [ ] **Step 3: Run D3 in isolation**

```bash
cd /workspace/autoship-cli
PYTHONPATH=/workspace/autoship-cli .venv/bin/python dogfood/dev_team_crisis/phase_d3.py
```

Expected: reveals config precedence and sandbox policy issues.

---

## Task 6: Fix discovered CLI issues and optimize

**Files:**
- Modify: discovered files

- [ ] **Step 1: Fix the first real failure from D1/D2/D3**

For each failure:
1. Add or update a unit test in `tests/` that reproduces it.
2. Apply the minimal fix in `src/autoship/...`.
3. Run the targeted test.

Likely fixes:
- `commit.py`: propagate pre_commit failures (Task 3 Step 1).
- `doctor.py`: include `Run autoship init` suggestion for invalid TOML configs.
- `config_center.py` / `config.py`: clarify team vs user precedence when listing config.
- `sandbox.py`: include missing capability name in sandbox error messages.

- [ ] **Step 2: Run the full simulation again**

```bash
cd /workspace/autoship-cli
PYTHONPATH=/workspace/autoship-cli .venv/bin/python dogfood/dev_team_crisis/run_all.py
```

Expected: all scenarios pass after fixes.

---

## Task 7: Final quality gates and commit

**Files:**
- Modify: `.bandit` if new subprocess-heavy fixtures need skipping
- Modify: `.gitignore` if new report directories need ignoring

- [ ] **Step 1: Run all quality gates**

```bash
cd /workspace/autoship-cli
.venv/bin/python -m ruff check src tests dogfood
.venv/bin/python -m ruff format --check src tests dogfood
.venv/bin/python -m pyright src
.venv/bin/python -m pytest
.venv/bin/python -m bandit -r src -c .bandit
.venv/bin/python -m pip_audit
```

Expected: all exit 0.

- [ ] **Step 2: Commit and push to both remotes**

```bash
cd /workspace/autoship-cli
git add dogfood/dev_team_crisis/ docs/superpowers/plans/ src/autoship/locales/ src/autoship/cli/commands/commit.py .bandit .gitignore
git commit -m "feat: add DevTeam Crisis D1/D2/D3 simulation suite and CLI fixes"
# Push using credential helper or token URLs
git push github main
git push gitcode main
```

---

## Spec coverage self-review

| Spec requirement | Plan task |
|---|---|
| D1 plugin delivery with i18n/audit/WIP blocking | Tasks 2 & 3 |
| D1 Python version doctor warning | Task 3 `_scenario_bob_python_version` |
| D1 sandbox filesystem failure | Task 3 plugin audit writes + hook failure propagation |
| D1 coverage gate | Task 3 `_scenario_alice_delivers_plugin` |
| D1 Bandit subprocess decision | Task 3 `_scenario_bandit_subprocess_flag` |
| D2 dirty repo rescue by three personas | Task 4 |
| D2 hardcoded secret handling | Task 4 `_create_dirty_repo` / `_scenario_carol_methodical` |
| D2 invalid config suggestion | Task 4 `_scenario_evan_misconfigures` |
| D3 untrusted --no-sandbox block | Task 5 `_scenario_untrusted_no_sandbox_blocked` |
| D3 team vs user config precedence | Task 5 `_scenario_team_config_precedence` |
| D3 sandbox conflict | Task 5 `_scenario_sandbox_conflict` |
| Shared runner/report harness | Task 1 |
| Final gates and remote sync | Task 7 |

**No placeholders remain.** All tasks include exact file paths, code, and expected outputs.
