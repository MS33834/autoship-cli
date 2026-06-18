"""Tests for the verify command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from autoship.cli.commands import verify
from autoship.exceptions import VerifyError
from autoship.models.config import AppConfig


def test_verify_success(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "OK"
        mock_run.return_value.stderr = ""
        verify.verify(ctx, command="echo ok")


def test_verify_failure(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "FAILED"
        with pytest.raises(VerifyError):
            verify.verify(ctx, command="false")


def test_verify_dry_run(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": True,
        "yes": True,
        "verbose": False,
    }
    with pytest.raises(verify.typer.Exit) as exc:
        verify.verify(ctx, command="echo ok")
    assert exc.value.exit_code == 0
