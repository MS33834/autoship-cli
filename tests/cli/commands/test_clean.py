"""Tests for the clean command."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from autoship.cli.commands import clean
from autoship.cli.main import app
from autoship.exceptions import ToolChainError
from autoship.models.config import AppConfig


def test_clean_noop_when_already_clean(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with patch("shutil.which", return_value=None):
        clean.clean(ctx, paths=[Path(".")], check=False)


def test_clean_check_raises_when_changes_needed(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with (
        patch.object(clean.ToolChain, "preview", return_value="--- diff ---"),
        pytest.raises(ToolChainError),
    ):
        clean.clean(ctx, paths=[Path(".")], check=True)


def test_clean_preview_failure_raises_toolchain_error(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with (
        patch.object(clean.ToolChain, "preview", side_effect=subprocess.CalledProcessError(1, [])),
        pytest.raises(ToolChainError, match="Failed to preview"),
    ):
        clean.clean(ctx, paths=[Path(".")], check=False)


def test_clean_apply_failure_raises_toolchain_error(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with (
        patch.object(clean.ToolChain, "preview", return_value="--- diff ---"),
        patch.object(clean.ToolChain, "apply", side_effect=subprocess.CalledProcessError(1, [])),
        pytest.raises(ToolChainError, match="Failed to apply"),
    ):
        clean.clean(ctx, paths=[Path(".")], check=False)


def test_clean_yes_option_skips_confirmation(app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": False,
        "verbose": False,
    }
    with (
        patch.object(clean.ToolChain, "preview", return_value="--- diff ---"),
        patch.object(clean.ToolChain, "apply") as mock_apply,
    ):
        clean.clean(ctx, paths=[Path(".")], check=False, yes=True)
        mock_apply.assert_called_once()


runner = CliRunner()


def test_clean_subcommand_yes_skips_confirm() -> None:
    with (
        patch.object(clean.ToolChain, "preview", return_value="--- diff ---"),
        patch.object(clean.ToolChain, "apply") as mock_apply,
    ):
        result = runner.invoke(app, ["clean", "--yes"])
    assert result.exit_code == 0
    mock_apply.assert_called_once()


def test_clean_global_yes_still_skips_confirm() -> None:
    with (
        patch.object(clean.ToolChain, "preview", return_value="--- diff ---"),
        patch.object(clean.ToolChain, "apply") as mock_apply,
    ):
        result = runner.invoke(app, ["--yes", "clean"])
    assert result.exit_code == 0
    mock_apply.assert_called_once()
