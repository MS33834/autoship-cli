"""Tests for the doctor command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from autoship.cli.main import app

runner = CliRunner()


def test_doctor_runs_and_reports_summary() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code in (0, 1)
    assert "AutoShip Environment Diagnostics" in result.output
    assert "Summary:" in result.output


def test_doctor_json_output() -> None:
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code in (0, 1)
    assert '"summary"' in result.output
    assert '"checks"' in result.output


def test_doctor_detects_missing_git() -> None:
    with patch("autoship.cli.commands.doctor._run_cmd", return_value=(False, "not found")):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "Git not found" in result.output


def test_doctor_detects_old_python() -> None:
    from autoship.cli.commands.doctor import CheckResult, Status

    with patch("autoship.cli.commands.doctor.check_python", return_value=CheckResult(
        name="python",
        status=Status.ERROR,
        message="Python 3.9.0",
        suggestion="Upgrade to Python 3.10 or later.",
    )):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "Python 3.9" in result.output
