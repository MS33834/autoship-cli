"""Tests for the clean command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autoship.cli.commands import clean
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
        clean.clean(ctx, paths=[Path(".")])


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
