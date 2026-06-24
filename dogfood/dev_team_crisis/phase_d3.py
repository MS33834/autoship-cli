"""D3 — Multi-developer policy conflict."""

from __future__ import annotations

import tempfile
from pathlib import Path

from dogfood.dev_team_crisis.runner import (
    Scenario,
    Step,
    install_local_plugin,
    run_autoship,
    setup_git,
    uninstall_plugin,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMUNITY_PLUGIN_DIR = (
    REPO_ROOT / "dogfood" / "dev_team_crisis" / "fixtures" / "community_echo_plugin"
)


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
            [
                "plugin",
                "install",
                str(COMMUNITY_PLUGIN_DIR),
                "--trust",
                "untrusted",
                "--no-sandbox",
                "--yes",
            ],
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
            'schema_version = 1\n[verify]\nallowed_commands = ["pytest", "python"]\n',
        )
        _write_file(
            root / ".autoship.team.toml",
            'schema_version = 1\n[verify]\nallowed_commands = ["pytest", "bandit"]\n',
        )
        _write_file(root / "tests" / "test_dummy.py", "def test_dummy():\n    pass\n")

        cfg = run_autoship(
            ["config", "get", "verify.allowed_commands"],
            cwd=root,
        )
        scenario.steps.append(cfg)

        if cfg.rc == 0:
            team_wins = "bandit" in cfg.stdout and "python" not in cfg.stdout
        else:
            # `config get` is unavailable; fall back to `verify pytest` so we
            # still exercise the config loader and can inspect runtime behavior.
            verify = run_autoship(["verify", "pytest"], cwd=root)
            scenario.steps.append(verify)
            team_wins = False

        scenario.steps.append(
            Step(
                name="assert team config takes precedence",
                rc=0 if team_wins else 1,
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
        _write_file(
            root / ".autoship.team.toml",
            "schema_version = 1\n[sandbox]\nrequired = true\n",
        )
        # Community plugin install without --no-sandbox should still work (sandbox enforced).
        scenario.steps.append(
            install_local_plugin(COMMUNITY_PLUGIN_DIR, "community_echo", trust="community")
        )
        # Trigger a hook call; sandboxed plugin should still run.
        scenario.steps.append(run_autoship(["doctor"], cwd=root))
        scenario.steps.append(uninstall_plugin("community_echo"))
    return scenario


def run_all() -> list[Scenario]:
    """Run all D3 scenarios."""
    return [
        _scenario_untrusted_no_sandbox_blocked(),
        _scenario_team_config_precedence(),
        _scenario_sandbox_conflict(),
    ]


if __name__ == "__main__":
    scenarios = run_all()
    total_steps = sum(len(s.steps) for s in scenarios)
    passed_steps = sum(1 for s in scenarios for step in s.steps if step.passed)
    passed_scenarios = sum(1 for s in scenarios if s.passed)

    print("=== D3: Multi-developer policy conflict ===")
    for scenario in scenarios:
        status = "PASS" if scenario.passed else "FAIL"
        print(f"{scenario.name}: {status}")
        for step in scenario.steps:
            step_status = "PASS" if step.passed else "FAIL"
            print(f"  [{step_status}] {step.name} (rc={step.rc})")
            if not step.passed and step.stderr:
                snippet = step.stderr.strip().replace("\n", " ")[:160]
                print(f"      {snippet}")

    print(
        f"\nSummary: {passed_scenarios}/{len(scenarios)} scenarios, "
        f"{passed_steps}/{total_steps} steps passed"
    )
