"""Phase C — fault-injection drills for AutoShip-CLI."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from dogfood.real_world.runner import (
    Scenario,
    Step,
    run_autoship,
    setup_git,
)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scenario_corrupt_config() -> Scenario:
    """Inject an invalid TOML config and verify graceful failure."""
    scenario = Scenario(
        name="corrupt_config",
        description="A malformed .autoship.toml is rejected with a clear config error.",
        persona="Chaos engineer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / ".autoship.toml", "schema_version = 1\nproject_type = 'generic'\n[broken\n"
        )
        setup_git(root)
        doctor_step = run_autoship(["doctor"], cwd=root, expected="fail")
        scenario.steps.append(doctor_step)
        scenario.steps.append(
            Step(
                name="assert config error suggestion",
                rc=0 if "Run `autoship init`" in (doctor_step.stdout + doctor_step.stderr) else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
        scenario.steps.append(
            Step(
                name="assert config error exit code",
                rc=0 if doctor_step.rc == 2 else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_disallowed_verify_command() -> Scenario:
    """Try to run a shell command not on the verify allowlist."""
    scenario = Scenario(
        name="disallowed_verify_command",
        description="`autoship verify ls` is rejected because `ls` is not in the allowlist.",
        persona="Security engineer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / ".autoship.toml",
            "schema_version = 1\nproject_type = 'generic'\n",
        )
        setup_git(root)
        step = run_autoship(["verify", "ls"], cwd=root, expected="fail")
        scenario.steps.append(step)
        scenario.steps.append(
            Step(
                name="assert command_disallowed",
                rc=0 if "not allowed" in step.stdout + step.stderr else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_missing_verify_command() -> Scenario:
    """Try to run a non-existent but allowlisted command."""
    scenario = Scenario(
        name="missing_verify_command",
        description="`autoship verify nonexistent-tool-xyz` fails with command_not_found.",
        persona="Platform engineer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / ".autoship.toml",
            """schema_version = 1
project_type = "generic"

[verify]
allowed_commands = ["nonexistent-tool-xyz"]
""",
        )
        setup_git(root)
        step = run_autoship(["verify", "nonexistent-tool-xyz"], cwd=root, expected="fail")
        scenario.steps.append(step)
        scenario.steps.append(
            Step(
                name="assert command_not_found",
                rc=0 if "not found on PATH" in step.stdout + step.stderr else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_corrupt_plugin_registry() -> Scenario:
    """Corrupt the local plugin registry and confirm graceful degradation."""
    scenario = Scenario(
        name="corrupt_plugin_registry",
        description="A corrupt registry.json is tolerated; plugin list still works.",
        persona="Reliability engineer",
    )
    registry_dir = Path.home() / ".config" / "autoship"
    registry_file = registry_dir / "registry.json"
    backup: Path | None = None
    existed = registry_file.exists()
    if existed:
        backup = registry_file.with_suffix(".json.bak")
        shutil.copy2(registry_file, backup)
    registry_dir.mkdir(parents=True, exist_ok=True)
    registry_file.write_text("{ not valid json", encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_file(
                root / ".autoship.toml",
                "schema_version = 1\nproject_type = 'generic'\n",
            )
            setup_git(root)
            scenario.steps.append(run_autoship(["plugin", "list"], cwd=root))
    finally:
        if backup:
            shutil.copy2(backup, registry_file)
            backup.unlink()
        elif existed:
            pass
        else:
            registry_file.unlink(missing_ok=True)
    return scenario


def _scenario_readonly_cache_dir() -> Scenario:
    """Make the cache directory read-only and confirm doctor reports it."""
    scenario = Scenario(
        name="readonly_cache_dir",
        description="A read-only cache directory causes doctor to report a cache warning or error.",
        persona="SRE",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Use a regular file as the cache dir so DiskCache initialization fails
        # with an OSError regardless of the user running the test.
        cache_dir = root / "readonly_cache"
        cache_dir.write_text("not a directory", encoding="utf-8")
        _write_file(
            root / ".autoship.toml",
            "schema_version = 1\nproject_type = 'generic'\n",
        )
        setup_git(root)
        step = run_autoship(
            ["doctor", "--json"],
            cwd=root,
            extra_env={"AUTOSHIP_CACHE__DIR": str(cache_dir)},
        )
        scenario.steps.append(step)
        doctor_data = json.loads(step.stdout)
        cache_check = next(
            (c for c in doctor_data.get("checks", []) if c.get("name") == "cache"), {}
        )
        status = cache_check.get("status", "")
        scenario.steps.append(
            Step(
                name="assert doctor cache warning/error",
                rc=0 if status in ("WARNING", "ERROR") else 1,
                stdout=f"cache status: {status}",
                stderr="",
                expected="success",
            )
        )
    return scenario


def _scenario_sensitive_env_blocked() -> Scenario:
    """Confirm sensitive environment overrides are blocked from config output."""
    scenario = Scenario(
        name="sensitive_env_blocked",
        description="AUTOSHIP_LLM__API_KEY is ignored and never surfaced by config or audit commands.",
        persona="Security auditor",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / ".autoship.toml",
            "schema_version = 1\nproject_type = 'generic'\n",
        )
        setup_git(root)
        secret = "sk-live-fault-injection-secret"
        extra_env = {"AUTOSHIP_LLM__API_KEY": secret}
        config_step = run_autoship(["config", "list", "--json"], cwd=root, extra_env=extra_env)
        audit_step = run_autoship(["audit", "export"], cwd=root, extra_env=extra_env)
        leaked = secret in (
            config_step.stdout + config_step.stderr + audit_step.stdout + audit_step.stderr
        )
        scenario.steps.extend(
            [
                config_step,
                audit_step,
                Step(
                    name="assert secret not leaked",
                    rc=0 if not leaked else 1,
                    stdout="" if not leaked else "sensitive value leaked",
                    stderr="",
                    expected="success",
                ),
            ]
        )
    return scenario


def _scenario_missing_clean_tool() -> Scenario:
    """Configure a non-existent clean tool and verify doctor reports it."""
    scenario = Scenario(
        name="missing_clean_tool",
        description='`clean.tools = ["zzblack"]` causes doctor to warn and clean to noop.',
        persona="Tooling engineer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / ".autoship.toml",
            """schema_version = 1
project_type = "generic"

[clean]
tools = ["zzblack"]
""",
        )
        setup_git(root)
        doctor_step = run_autoship(["doctor"], cwd=root)
        scenario.steps.append(doctor_step)
        scenario.steps.append(
            Step(
                name="assert doctor clean warning",
                rc=0 if "zzblack" in doctor_step.stdout + doctor_step.stderr else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
        scenario.steps.append(run_autoship(["--yes", "clean"], cwd=root))
    return scenario


def _scenario_unreachable_model_backend() -> Scenario:
    """Point the model backend to an unreachable endpoint and verify graceful fallback."""
    scenario = Scenario(
        name="unreachable_model_backend",
        description="An unreachable model backend causes doctor to warn and commit to fall back to a default message.",
        persona="AI-integration engineer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / ".autoship.toml",
            """schema_version = 1
project_type = "generic"

[[model.backends]]
provider = "ollama"
base_url = "http://127.0.0.1:59999/v1"
model = "llama3"
tier = 1
""",
        )
        _write_file(root / "main.py", "print('hello')\n")
        setup_git(root)
        doctor_step = run_autoship(["doctor"], cwd=root)
        scenario.steps.append(doctor_step)
        scenario.steps.append(
            Step(
                name="assert doctor model unreachable",
                rc=0 if "not reachable" in doctor_step.stdout + doctor_step.stderr else 1,
                stdout="",
                stderr="",
                expected="success",
            )
        )
        commit_step = run_autoship(["--yes", "commit", "-m", "fallback commit message"], cwd=root)
        scenario.steps.append(commit_step)
    return scenario


def run_all() -> list[Scenario]:
    """Run all Phase C fault-injection scenarios."""
    return [
        _scenario_corrupt_config(),
        _scenario_disallowed_verify_command(),
        _scenario_missing_verify_command(),
        _scenario_corrupt_plugin_registry(),
        _scenario_readonly_cache_dir(),
        _scenario_sensitive_env_blocked(),
        _scenario_missing_clean_tool(),
        _scenario_unreachable_model_backend(),
    ]


if __name__ == "__main__":
    for scenario in run_all():
        print(f"{scenario.name}: {'PASS' if scenario.passed else 'FAIL'}")
