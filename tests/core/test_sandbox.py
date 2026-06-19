"""Tests for the sandbox runner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from autoship.core.sandbox import SandboxRunner


def test_sandbox_runs_command() -> None:
    runner = SandboxRunner(network=True)
    result = runner.run(["python", "-c", "print('hello')"])
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_sandbox_env_isolation() -> None:
    runner = SandboxRunner(network=True, env_whitelist=["PATH"])
    result = runner.run(["python", "-c", "import os; print(os.environ.get('AUTOSHIP_TEST', 'missing'))"])
    assert result.returncode == 0
    assert "missing" in result.stdout


def test_sandbox_uses_custom_working_dir(tmp_path: Path) -> None:
    runner = SandboxRunner(network=True, working_dir=tmp_path)
    result = runner.run(["python", "-c", "import os; print(os.getcwd())"])
    assert result.returncode == 0
    assert str(tmp_path) in result.stdout


def test_sandbox_returns_error_for_missing_command() -> None:
    runner = SandboxRunner(network=True)
    result = runner.run(["this-command-does-not-exist-12345"])
    assert result.returncode == -1
    assert result.stderr != ""


def test_sandbox_wraps_network_when_tool_available() -> None:
    runner = SandboxRunner(network=False)
    with patch("shutil.which", side_effect=["unshare", None]):
        wrapped = runner._wrap_network(["python", "-c", "pass"])
    assert wrapped[0] == "unshare"
    assert wrapped[1] == "--net"


def test_sandbox_falls_back_without_tool() -> None:
    runner = SandboxRunner(network=False)
    with patch("shutil.which", return_value=None):
        wrapped = runner._wrap_network(["python", "-c", "pass"])
    assert wrapped == ["python", "-c", "pass"]


def test_sandbox_available_reports_capabilities() -> None:
    runner = SandboxRunner(network=False)
    caps = runner.available()
    assert "network_unshare" in caps
    assert "network_firejail" in caps
    assert caps["directory_isolation"] is True
    assert caps["env_isolation"] is True
