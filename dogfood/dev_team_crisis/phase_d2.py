"""D2 — Pre-launch repo rescue by three personas."""

from __future__ import annotations

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

[tool.pytest.ini_options]
pythonpath = ["src"]
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
        # Capture the failing test so the subsequent fix command has an error log.
        scenario.steps.append(run_autoship(["verify", "pytest"], cwd=root, expected="fail"))
        # Fix failing test manually.
        _write_file(
            root / "tests/test_core.py",
            "from acme.core import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        )
        scenario.steps.append(run_autoship(["verify", "pytest"], cwd=root))
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(
                ["--yes", "commit", "-m", "fix(core): repair tests and remove secret"],
                cwd=root,
            )
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
        # First run a failing verification so there is an error log.
        scenario.steps.append(run_autoship(["verify", "pytest"], cwd=root, expected="fail"))
        # Dave expects fix to handle the failure, but no model backend is configured.
        step = run_autoship(["--yes", "fix"], cwd=root, expected="fail")
        scenario.steps.append(step)
        # Expect a clear message pointing to model backend configuration.
        output = (step.stdout + step.stderr).lower()
        actionable = "model backend" in output or "unhealthy" in output or "model" in output
        scenario.steps.append(
            Step(
                name="assert actionable backend error",
                rc=0 if actionable else 1,
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
    """Run all D2 scenarios."""
    return [
        _scenario_carol_methodical(),
        _scenario_dave_shortcut(),
        _scenario_evan_misconfigures(),
    ]


if __name__ == "__main__":
    scenarios = run_all()
    for scenario in scenarios:
        status = "PASS" if scenario.passed else "FAIL"
        print(f"{scenario.name}: {status}")
        for step in scenario.steps:
            if not step.passed:
                print(f"  FAIL: {step.name} (rc={step.rc})")
                if step.stdout:
                    print(f"    stdout: {step.stdout[:500]}")
                if step.stderr:
                    print(f"    stderr: {step.stderr[:500]}")
    sys.exit(0 if all(s.passed for s in scenarios) else 1)
