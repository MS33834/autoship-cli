"""End-to-end tests using Typer's CliRunner."""

from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from autoship.cli.main import app

runner = CliRunner()


def test_help_prints_usage() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AutoShip" in result.output


def test_init_creates_config(tmp_path: Path) -> None:
    config_path = tmp_path / ".autoship.toml"
    result = runner.invoke(
        app,
        ["--yes", "init", "--output", str(config_path)],
    )
    assert result.exit_code == 0
    assert config_path.exists()
    assert "project_type" in config_path.read_text(encoding="utf-8")


def test_clean_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--dry-run", "--yes", "clean", str(tmp_path)],
    )
    assert result.exit_code == 0


def test_verify_runs_command(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--yes", "verify", "echo ok"],
    )
    assert result.exit_code == 0
    assert "Verified" in result.output


def test_commit_with_yes(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "hello.txt").write_text("world")

    result = runner.invoke(
        app,
        ["--config", str(tmp_path / ".autoship.toml"), "--yes", "commit"],
    )
    assert result.exit_code == 0
    assert "Committed" in result.output


def test_upload_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--dry-run", "--yes", "upload", "--target", "pypi"],
    )
    assert result.exit_code == 0
    assert "Uploaded to pypi" in result.output
