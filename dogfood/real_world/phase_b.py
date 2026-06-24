"""Phase B — plugin ecosystem stress tests with four complex plugins."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from dogfood.real_world.runner import (
    Scenario,
    Step,
    install_local_plugin,
    run,
    run_autoship,
    set_plugin_trust,
    setup_git,
    uninstall_plugin,
)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_plugin(
    root: Path,
    package: str,
    entry_name: str,
    plugin_code: str,
    test_code: str,
) -> Path:
    """Write a complete local plugin package under ``root``."""
    src_dir = root / "src" / package
    _write_file(src_dir / "__init__.py", "")
    _write_file(src_dir / "plugin.py", plugin_code)
    _write_file(
        root / "pyproject.toml",
        f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{package.replace("_", "-")}"
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
{entry_name} = "{package}.plugin:register"
""",
    )
    _write_file(root / "tests" / "test_plugin.py", test_code)
    return root


_LIFECYCLE_PLUGIN = """\
from __future__ import annotations

from pathlib import Path

from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion


class LifecycleLoggerPlugin(Plugin):
    @hook
    def pre_init(self, context: CommandContext) -> None:
        self._log(context, "pre_init")

    @hook
    def post_init(self, context: CommandContext) -> None:
        self._log(context, "post_init")

    @hook
    def pre_clean(self, context: CommandContext) -> None:
        self._log(context, "pre_clean")

    @hook
    def post_clean(self, context: CommandContext) -> None:
        self._log(context, "post_clean")

    @hook
    def pre_commit(self, context: CommandContext) -> None:
        self._log(context, "pre_commit")

    @hook
    def post_commit(self, context: CommandContext) -> None:
        self._log(context, "post_commit")

    @hook
    def pre_verify(self, context: CommandContext) -> None:
        self._log(context, "pre_verify")

    @hook
    def post_verify(self, context: CommandContext) -> None:
        self._log(context, "post_verify")

    @hook
    def pre_upload(self, context: CommandContext) -> None:
        self._log(context, "pre_upload")

    @hook
    def post_upload(self, context: CommandContext) -> None:
        self._log(context, "post_upload")

    @hook
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        self._log(context, "on_error")
        return None

    def _log(self, context: CommandContext, hook_name: str) -> None:
        log_dir = context.project_root / ".autoship"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "lifecycle.log"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"{hook_name}\\n")
        print(f"[lifecycle] {hook_name}")


def register() -> LifecycleLoggerPlugin:
    return LifecycleLoggerPlugin()
"""

_LIFECYCLE_TEST = """\
from autoship_hello_plugin_lifecycle.plugin import LifecycleLoggerPlugin
from autoship_sdk.testing import PluginTestHarness


def test_all_hooks_logged(tmp_path):
    plugin = LifecycleLoggerPlugin()
    harness = PluginTestHarness()
    harness.register(plugin)
    ctx = harness.make_context("verify", project_root=tmp_path)
    for hook_name in ("pre_init", "post_init", "pre_verify", "post_verify"):
        harness.call(hook_name, ctx)
    log_file = tmp_path / ".autoship" / "lifecycle.log"
    assert log_file.exists()
    lines = log_file.read_text().splitlines()
    assert "pre_verify" in lines
    assert "post_verify" in lines
"""

_POLICY_PLUGIN = """\
from __future__ import annotations

import subprocess
from pathlib import Path

from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion


class PolicyGuardPlugin(Plugin):
    @hook
    def pre_verify(self, context: CommandContext) -> None:
        python_files = list(context.project_root.rglob("*.py"))
        if not python_files:
            return
        cmd = ["python", "-m", "py_compile"] + [str(p) for p in python_files[:50]]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("[policy-guard] Syntax error detected before running tests.")

    @hook
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        if not context.extras.get("fix"):
            return None
        target = context.project_root / "src" / "targetapp" / "greeter.py"
        if not target.exists():
            return None
        old = target.read_text(encoding="utf-8")
        new = old.replace("return greetting", 'return "hello"')
        if new == old:
            return None
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = [
            "diff --git a/src/targetapp/greeter.py b/src/targetapp/greeter.py",
            "--- a/src/targetapp/greeter.py",
            "+++ b/src/targetapp/greeter.py",
        ]
        for i, (a, b) in enumerate(zip(old_lines, new_lines), start=1):
            if a != b:
                diff.append(f"@@ -{i},1 +{i},1 @@")
                diff.append(f"-{a.rstrip()}")
                diff.append(f"+{b.rstrip()}")
        patch = "\\n".join(diff) + "\\n"
        return FixSuggestion(
            description="[policy-guard] Fix undefined name 'greetting'.",
            patch=patch,
        )


def register() -> PolicyGuardPlugin:
    return PolicyGuardPlugin()
"""

_POLICY_TEST = """\
from autoship_policy_guard.plugin import PolicyGuardPlugin
from autoship_sdk.testing import PluginTestHarness


def test_on_error_returns_suggestion(tmp_path):
    plugin = PolicyGuardPlugin()
    harness = PluginTestHarness()
    harness.register(plugin)
    src = tmp_path / "src" / "targetapp"
    src.mkdir(parents=True)
    (src / "greeter.py").write_text("def greet():\\n    return greetting\\n", encoding="utf-8")
    ctx = harness.make_context("verify", project_root=tmp_path, extras={"fix": True})
    result = harness.call("on_error", ctx, error=RuntimeError("verify failed"))
    assert len(result) == 1
    assert "greetting" in result[0].description
    assert "hello" in result[0].patch
"""

_NETWORK_PLUGIN = """\
from __future__ import annotations

import socket
from pathlib import Path

from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class NetworkProbePlugin(Plugin):
    @hook
    def pre_verify(self, context: CommandContext) -> None:
        status_file = context.project_root / ".autoship" / "network_status.txt"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with socket.create_connection(("example.com", 80), timeout=5):
                status_file.write_text("reachable", encoding="utf-8")
        except OSError:
            status_file.write_text("blocked", encoding="utf-8")


def register() -> NetworkProbePlugin:
    return NetworkProbePlugin()
"""

_NETWORK_TEST = """\
from autoship_network_probe.plugin import NetworkProbePlugin
from autoship_sdk.testing import PluginTestHarness


def test_probe_writes_status(tmp_path):
    plugin = NetworkProbePlugin()
    harness = PluginTestHarness()
    harness.register(plugin)
    ctx = harness.make_context("verify", project_root=tmp_path)
    harness.call("pre_verify", ctx)
    status = (tmp_path / ".autoship" / "network_status.txt").read_text(encoding="utf-8")
    assert status in ("reachable", "blocked")
"""

_FAULTY_PLUGIN = """\
from __future__ import annotations

from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class FaultyHookPlugin(Plugin):
    @hook
    def pre_commit(self, context: CommandContext) -> None:
        raise ValueError("intentional plugin fault")


def register() -> FaultyHookPlugin:
    return FaultyHookPlugin()
"""

_FAULTY_TEST = """\
import pytest
from autoship_faulty_hook.plugin import FaultyHookPlugin
from autoship_sdk.testing import PluginTestHarness


def test_faulty_hook_raises():
    plugin = FaultyHookPlugin()
    harness = PluginTestHarness()
    harness.register(plugin)
    ctx = harness.make_context("commit")
    with pytest.raises(Exception):
        harness.call("pre_commit", ctx, fail_fast=True)
"""


def _target_project(root: Path) -> None:
    """Create a small target project for multi-plugin interaction."""
    _write_file(
        root / "pyproject.toml",
        """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "targetapp"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
""",
    )
    _write_file(root / "src/targetapp/__init__.py", "")
    _write_file(
        root / "src/targetapp/greeter.py",
        """def greet():
    return greetting
""",
    )
    _write_file(
        root / "tests/test_greeter.py",
        """from targetapp.greeter import greet

def test_greet():
    assert greet() == "hello"
""",
    )
    setup_git(root)


def _run_plugin_unit_tests(plugin_dir: Path) -> Step:
    """Run a plugin's own pytest suite with its ``src`` on PYTHONPATH."""
    extra_env = {"PYTHONPATH": str(plugin_dir / "src")}
    result = run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=plugin_dir,
        timeout=60,
        extra_env=extra_env,
    )
    return Step(
        name=f"pytest {plugin_dir.name}",
        rc=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        expected="success",
    )


def run_all() -> list[Scenario]:
    """Run all Phase B scenarios."""
    scenarios: list[Scenario] = []

    with tempfile.TemporaryDirectory() as plugins_tmp:
        plugins_root = Path(plugins_tmp)
        lifecycle_dir = plugins_root / "lifecycle"
        policy_dir = plugins_root / "policy"
        network_dir = plugins_root / "network"
        faulty_dir = plugins_root / "faulty"

        _build_plugin(
            lifecycle_dir,
            "autoship_hello_plugin_lifecycle",
            "lifecycle",
            _LIFECYCLE_PLUGIN,
            _LIFECYCLE_TEST,
        )
        _build_plugin(policy_dir, "autoship_policy_guard", "policy", _POLICY_PLUGIN, _POLICY_TEST)
        _build_plugin(
            network_dir,
            "autoship_network_probe",
            "network",
            _NETWORK_PLUGIN,
            _NETWORK_TEST,
        )
        _build_plugin(faulty_dir, "autoship_faulty_hook", "faulty", _FAULTY_PLUGIN, _FAULTY_TEST)

        # Isolated unit tests for each plugin.
        harness_scenario = Scenario(
            name="plugin_unit_tests",
            description="Each complex plugin passes its own pytest suite in isolation.",
            persona="Plugin QA engineer",
        )
        for plugin_dir in (lifecycle_dir, policy_dir, network_dir, faulty_dir):
            harness_scenario.steps.append(_run_plugin_unit_tests(plugin_dir))
        scenarios.append(harness_scenario)

        # Install plugins and exercise them together in a target project.
        interaction_scenario = Scenario(
            name="plugin_interactions",
            description="Install all four plugins into a target project and run CLI commands.",
            persona="Integration tester",
        )
        with tempfile.TemporaryDirectory() as target_tmp:
            target_root = Path(target_tmp)
            _target_project(target_root)

            interaction_scenario.steps.append(run_autoship(["init", "--yes"], cwd=target_root))
            interaction_scenario.steps.append(install_local_plugin(lifecycle_dir, "lifecycle"))
            interaction_scenario.steps.append(install_local_plugin(policy_dir, "policy"))
            interaction_scenario.steps.append(install_local_plugin(network_dir, "network"))
            interaction_scenario.steps.append(install_local_plugin(faulty_dir, "faulty"))
            interaction_scenario.steps.append(run_autoship(["plugin", "list"], cwd=target_root))

            # Verify triggers lifecycle + policy + network hooks; policy returns patch when --fix.
            # The original verify still fails, so this command is expected to fail.
            interaction_scenario.steps.append(
                run_autoship(
                    ["--yes", "verify", "pytest", "--fix"], cwd=target_root, expected="fail"
                )
            )
            # After the patch is applied, re-running verify should pass.
            interaction_scenario.steps.append(
                run_autoship(["verify", "pytest"], cwd=target_root, expected="success")
            )

            # Commit triggers lifecycle + faulty hooks; faulty is logged but commit succeeds.
            commit_step = run_autoship(
                ["--yes", "commit", "-m", "chore: plugin stress test"],
                cwd=target_root,
            )
            interaction_scenario.steps.append(commit_step)

            # Upload dry-run triggers lifecycle hooks.
            interaction_scenario.steps.append(
                run_autoship(
                    ["--yes", "--dry-run", "upload", "--target", "pypi"],
                    cwd=target_root,
                )
            )

            # Test community/sandbox trust: network probe should report blocked network.
            interaction_scenario.steps.append(set_plugin_trust("network", "community"))
            verify_sandbox_step = run_autoship(["--yes", "verify", "pytest"], cwd=target_root)
            interaction_scenario.steps.append(verify_sandbox_step)
            status_file = target_root / ".autoship" / "network_status.txt"
            network_blocked = (
                status_file.exists() and status_file.read_text(encoding="utf-8") == "blocked"
            )
            interaction_scenario.steps.append(
                Step(
                    name="assert network sandbox blocked",
                    rc=0 if network_blocked else 1,
                    stdout="" if network_blocked else "expected sandbox to block network",
                    stderr="",
                    expected="success",
                )
            )

            # Faulty hook should be tolerated.
            faulty_logged = "intentional plugin fault" in commit_step.stderr
            interaction_scenario.steps.append(
                Step(
                    name="assert faulty hook tolerated",
                    rc=0 if faulty_logged else 1,
                    stdout="" if faulty_logged else "expected faulty hook to be logged",
                    stderr="",
                    expected="success",
                )
            )

            for name in ("lifecycle", "policy", "network", "faulty"):
                interaction_scenario.steps.append(uninstall_plugin(name))

        scenarios.append(interaction_scenario)

    return scenarios


if __name__ == "__main__":
    import sys

    for scenario in run_all():
        print(f"{scenario.name}: {'PASS' if scenario.passed else 'FAIL'}")
