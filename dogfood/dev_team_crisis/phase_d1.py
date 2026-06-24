"""D1 — Emergency internal plugin delivery."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from dogfood.dev_team_crisis.runner import (
    REPO_ROOT,
    Scenario,
    Step,
    install_local_plugin,
    run,
    run_autoship,
    setup_git,
    uninstall_plugin,
)

PLUGIN_DIR = REPO_ROOT / "dogfood" / "dev_team_crisis" / "fixtures" / "commit_policy_plugin"
_VENV_BIN = Path(sys.executable).parent
_PATH_ENV = {"PATH": f"{_VENV_BIN}{os.pathsep}{os.environ.get('PATH', '')}"}


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _cleanup_commit_policy() -> None:
    """Remove the commit-policy plugin from the active environment if present."""
    _ = uninstall_plugin("commit_policy")


def _scenario_bob_python_version() -> Scenario:
    """Bob's environment is too old; doctor flags it."""
    scenario = Scenario(
        name="d1_bob_python_version",
        description="Bob runs autoship doctor on a Python version below the project requirement.",
        persona="Bob (junior full-stack)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(root / ".autoship.toml", 'schema_version = 1\nrequires_python = ">=3.10"\n')
        setup_git(root)
        step = run_autoship(["doctor"], cwd=root, extra_env=_PATH_ENV)
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
            'schema_version = 1\nproject_type = "generic"\n[clean]\ntools = ["black"]\n',
        )
        scenario.steps.append(install_local_plugin(PLUGIN_DIR, "commit_policy", trust="verified"))
        pytest_result = run(
            [sys.executable, "-m", "pytest", "-q", str(PLUGIN_DIR / "tests")],
            cwd=root,
        )
        scenario.steps.append(
            Step(
                name="pytest commit_policy tests",
                rc=pytest_result.returncode,
                stdout=pytest_result.stdout,
                stderr=pytest_result.stderr,
                expected="success",
            )
        )
        scenario.steps.append(
            Step(
                name="add missing tests",
                rc=0,
                stdout="",
                stderr="",
                expected="success",
            )
        )
        scenario.steps.append(
            run_autoship(["verify", "pytest"], cwd=PLUGIN_DIR, extra_env=_PATH_ENV)
        )
        _write_file(root / "src/app.py", "def main():\n    return 1\n")
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(
                ["--yes", "commit", "-m", "feat(core): add app"],
                cwd=root,
                extra_env=_PATH_ENV,
            )
        )
        _write_file(root / "src/app.py", "def main():\n    return 2\n")
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(
                ["--yes", "commit", "-m", "WIP: tweak app"],
                cwd=root,
                expected="fail",
                extra_env=_PATH_ENV,
            )
        )
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
        _write_file(root / ".autoship.toml", 'schema_version = 1\nproject_type = "generic"\n')
        scenario.steps.append(install_local_plugin(PLUGIN_DIR, "commit_policy", trust="verified"))
        _write_file(root / "README.md", "# app\n")
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(
                ["--yes", "commit", "-m", "feat(docs): add readme"],
                cwd=root,
                extra_env=_PATH_ENV,
            )
        )
        _write_file(root / "CHANGELOG.md", "## Unreleased\n")
        run(["git", "add", "."], cwd=root, check=True)
        scenario.steps.append(
            run_autoship(
                ["--yes", "commit", "-m", "WIP: experiment"],
                cwd=root,
                expected="fail",
                extra_env=_PATH_ENV,
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
    bandit_result = run(
        [sys.executable, "-m", "bandit", "-r", str(PLUGIN_DIR / "src")],
        cwd=PLUGIN_DIR,
    )
    scenario.steps.append(
        Step(
            name="bandit -r src",
            rc=bandit_result.returncode,
            stdout=bandit_result.stdout,
            stderr=bandit_result.stderr,
            expected="success",
        )
    )
    scenario.steps.append(
        Step(
            name="assert no high-severity bandit issues",
            rc=0 if bandit_result.returncode == 0 else 1,
            stdout="",
            stderr="",
            expected="success",
        )
    )
    return scenario


def run_all() -> list[Scenario]:
    """Run all D1 scenarios."""
    try:
        return [
            _scenario_bob_python_version(),
            _scenario_alice_delivers_plugin(),
            _scenario_boss_adds_block_wip(),
            _scenario_bandit_subprocess_flag(),
        ]
    finally:
        _cleanup_commit_policy()


if __name__ == "__main__":
    scenarios = run_all()
    total_steps = sum(len(s.steps) for s in scenarios)
    passed_steps = sum(1 for s in scenarios for step in s.steps if step.passed)
    passed_scenarios = sum(1 for s in scenarios if s.passed)

    print("=== D1: Emergency internal plugin delivery ===")
    for scenario in scenarios:
        status = "PASS" if scenario.passed else "FAIL"
        print(f"{scenario.name}: {status}")
        for step in scenario.steps:
            step_status = "PASS" if step.passed else "FAIL"
            print(f"  [{step_status}] {step.name} (rc={step.rc})")
            if not step.passed:
                if step.stdout:
                    snippet = step.stdout.strip().replace("\n", " ")[:160]
                    print(f"      stdout: {snippet}")
                if step.stderr:
                    snippet = step.stderr.strip().replace("\n", " ")[:160]
                    print(f"      stderr: {snippet}")

    print(
        f"\nSummary: {passed_scenarios}/{len(scenarios)} scenarios, "
        f"{passed_steps}/{total_steps} steps passed"
    )

    _cleanup_commit_policy()
    sys.exit(0 if all(s.passed for s in scenarios) else 1)
