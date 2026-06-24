"""Shared utilities for the real-world ABC validation harness."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
AUTOSHIP = [sys.executable, "-m", "autoship"]
CI = os.environ.get("CI", "false").lower() == "true"


def _env() -> dict[str, str]:
    """Return an environment that lets ``python -m autoship`` find source code."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["AUTOSHIP_LOG_LEVEL"] = "WARNING"
    # Ensure package installers such as ``uv`` can locate the active virtual environment
    # even when commands are executed from temporary working directories.
    if hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
        env["VIRTUAL_ENV"] = sys.prefix
    return env


def run(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = False,
    timeout: int = 120,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return a CompletedProcess, tolerating timeouts."""
    env = _env()
    if extra_env:
        env.update(extra_env)
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\n[timeout]"
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=stdout,
            stderr=stderr,
        )


def run_autoship(
    args: list[str],
    cwd: Path,
    expected: Literal["success", "fail", "skip"] = "success",
    timeout: int = 120,
    extra_env: dict[str, str] | None = None,
) -> Step:
    """Run ``autoship <args>`` and record the result as a Step."""
    result = run(AUTOSHIP + args, cwd=cwd, timeout=timeout, extra_env=extra_env)
    return Step(
        name="autoship " + " ".join(args),
        rc=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        expected=expected,
    )


def setup_git(project_root: Path) -> None:
    """Initialize a git repo with a deterministic identity."""
    run(["git", "init", "-q"], project_root, check=True)
    run(["git", "config", "user.email", "dogfood@example.com"], project_root, check=True)
    run(["git", "config", "user.name", "Dogfood"], project_root, check=True)


def ensure_clean_tools() -> None:
    """Make sure the default clean toolchain is available in the active environment."""
    missing = [tool for tool in ("black", "autoflake") if shutil.which(tool) is None]
    if not missing:
        return
    for installer in (
        [sys.executable, "-m", "pip", "install", *missing],
        ["uv", "pip", "install", *missing],
    ):
        if shutil.which(installer[0]):
            try:
                subprocess.run(installer, check=True, capture_output=True, text=True)
                return
            except (subprocess.CalledProcessError, FileNotFoundError, OSError):
                pass


def install_local_plugin(plugin_dir: Path, name: str, trust: str = "verified") -> Step:
    """Install a local plugin directory via ``autoship plugin install``."""
    return run_autoship(
        ["plugin", "install", str(plugin_dir), "--name", name, "--yes", "--trust", trust],
        cwd=plugin_dir,
        timeout=180,
    )


def uninstall_plugin(name: str) -> Step:
    """Uninstall a plugin via ``autoship plugin uninstall``."""
    return run_autoship(["plugin", "uninstall", name, "--yes"], cwd=REPO_ROOT, timeout=60)


def set_plugin_trust(name: str, level: str) -> Step:
    """Change a plugin's trust level."""
    return run_autoship(["plugin", "trust", name, level], cwd=REPO_ROOT, timeout=30)


@dataclass
class Step:
    """A single CLI invocation and its result."""

    name: str
    rc: int
    stdout: str
    stderr: str
    expected: Literal["success", "fail", "skip"]

    @property
    def passed(self) -> bool:
        if self.expected == "success":
            return self.rc == 0
        if self.expected == "fail":
            return self.rc != 0
        return True


@dataclass
class Scenario:
    """A named scenario composed of many steps."""

    name: str
    description: str
    persona: str
    steps: list[Step] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(step.passed for step in self.steps)


def render_report(title: str, scenarios: list[Scenario]) -> str:
    """Render a Markdown report for a list of scenarios."""
    lines = [
        f"# {title}",
        "",
        f"Python: {sys.version.split()[0]}",
        f"CI: {CI}",
        "",
        "## Scenarios",
        "",
    ]
    failed_steps: list[str] = []
    for scenario in scenarios:
        status = "PASS" if scenario.passed else "FAIL"
        lines.append(f"### {scenario.name} ({scenario.persona}) — {status}")
        lines.append(f"{scenario.description}")
        lines.append("")
        lines.append("| Command | Exit Code | Expected | Result |")
        lines.append("|---------|-----------|----------|--------|")
        for step in scenario.steps:
            result = "PASS" if step.passed else "FAIL"
            cmd_display = step.name.replace("|", "\\|")
            lines.append(f"| `{cmd_display}` | {step.rc} | {step.expected} | {result} |")
            if not step.passed:
                failed_steps.append(f"- `{scenario.name}` → `{step.name}` (rc={step.rc})")
                if step.stderr:
                    snippet = step.stderr.strip().replace("\n", " ")[:160]
                    failed_steps[-1] += f"\n  <small>{snippet}</small>"
        lines.append("")

    total = sum(len(s.steps) for s in scenarios)
    passed = sum(1 for s in scenarios for step in s.steps if step.passed)
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Steps passed: {passed} / {total}")
    lines.append(f"- Scenarios passed: {sum(1 for s in scenarios if s.passed)} / {len(scenarios)}")
    lines.append("")
    lines.append("## Failures")
    lines.append("")
    if failed_steps:
        lines.extend(failed_steps)
    else:
        lines.append("No unexpected failures.")
    lines.append("")
    return "\n".join(lines)


def write_json_report(
    title: str,
    scenarios: list[Scenario],
    path: Path,
) -> None:
    """Write a JSON report for a list of scenarios."""
    payload: dict[str, Any] = {
        "title": title,
        "python": sys.version.split()[0],
        "ci": CI,
        "scenarios": [
            {
                "name": s.name,
                "description": s.description,
                "persona": s.persona,
                "passed": s.passed,
                "steps": [
                    {
                        "command": step.name,
                        "rc": step.rc,
                        "expected": step.expected,
                        "passed": step.passed,
                        "stderr": step.stderr[:500] if step.stderr else "",
                    }
                    for step in s.steps
                ],
            }
            for s in scenarios
        ],
        "all_passed": all(s.passed for s in scenarios),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
