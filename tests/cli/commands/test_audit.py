"""Tests for the audit command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from autoship.cli.main import app

runner = CliRunner()


def _write_config(tmp_path: Path, log_dir: Path) -> Path:
    config_path = tmp_path / ".autoship.toml"
    config_path.write_text(
        f"""
schema_version = 1
project_root = "{tmp_path}"

[audit]
log_dir = "{log_dir}"
"""
    )
    return config_path


def test_audit_export_runs_and_creates_output(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    config_path = _write_config(tmp_path, log_dir)

    result = runner.invoke(app, ["--config", str(config_path), "audit", "export"])
    assert result.exit_code == 0
    assert "Exported" in result.output
    assert "records to" in result.output


def test_audit_export_with_since(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_file = log_dir / "audit.2020-01-01.jsonl"
    old_file.write_text('{"ts": "2020-01-01T00:00:00+00:00", "event": "old"}\n')
    config_path = _write_config(tmp_path, log_dir)

    result = runner.invoke(
        app,
        [
            "--config",
            str(config_path),
            "audit",
            "export",
            "--since",
            "2025-01-01",
        ],
    )
    assert result.exit_code == 0
    # The current cli.invoked record is included; the 2020 record is excluded.
    assert "Exported 1 records" in result.output


def test_audit_export_with_relative_since(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    config_path = _write_config(tmp_path, log_dir)

    result = runner.invoke(
        app,
        ["--config", str(config_path), "audit", "export", "--since", "1d"],
    )
    assert result.exit_code == 0
    assert "Exported" in result.output


def test_audit_cleanup_dry_run(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    config_path = _write_config(tmp_path, log_dir)

    result = runner.invoke(
        app,
        ["--config", str(config_path), "audit", "cleanup", "--dry-run"],
    )
    assert result.exit_code == 0
    assert "[dry-run]" in result.output


def test_audit_cleanup_removes_old_files(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_file = log_dir / "audit.2020-01-01.jsonl"
    old_file.write_text('{"ts": "2020-01-01T00:00:00+00:00"}\n')
    os.utime(old_file, (1, 1))
    config_path = _write_config(tmp_path, log_dir)

    result = runner.invoke(
        app,
        ["--config", str(config_path), "audit", "cleanup", "--retention-days", "30"],
    )
    assert result.exit_code == 0
    assert "Removed 1 old audit log files" in result.output
    assert not old_file.exists()
