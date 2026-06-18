"""Tests for the upload command."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from autoship.cli.commands import upload
from autoship.exceptions import ConfigError
from autoship.models.config import AppConfig


def test_upload_pypi_dry_run(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": True,
        "yes": True,
        "verbose": False,
    }
    upload.upload(ctx, target="pypi")


def test_upload_unknown_target(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": True,
        "yes": True,
        "verbose": False,
    }
    with pytest.raises(ConfigError):
        upload.upload(ctx, target="unknown")


def test_upload_user_abort(project_root, app_config: AppConfig, monkeypatch) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": False,
        "verbose": False,
    }
    monkeypatch.setattr(upload.typer, "confirm", lambda _: False)
    with pytest.raises(upload.typer.Exit) as exc:
        upload.upload(ctx, target="pypi")
    assert exc.value.exit_code == 0
