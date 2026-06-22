"""Tests for the main CLI entry point."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from autoship.cli import main
from autoship.exceptions import ConfigError, ExitCode


class FakeContext:
    """Minimal stand-in for a Typer context."""

    def __init__(self) -> None:
        self.obj: dict = {}

    def ensure_object(self, typ: type) -> None:
        if not self.obj:
            self.obj = {}


def test_main_callback_loads_config(tmp_path: Path) -> None:
    ctx = FakeContext()
    config_path = tmp_path / "autoship.toml"
    config_path.write_text("[model]\ndefault_tier = 1\n")

    main.main_callback(ctx, config_path=config_path)

    assert "config" in ctx.obj
    assert ctx.obj["config"].model.default_tier == 1
    assert "audit_logger" in ctx.obj


def test_main_callback_without_config() -> None:
    ctx = FakeContext()
    main.main_callback(ctx, config_path=None)
    assert "config" in ctx.obj
    assert "audit_logger" in ctx.obj


def test_cli_entrypoint_handles_autoship_error() -> None:
    error = ConfigError("bad config")
    mock_app = MagicMock(side_effect=error)
    with patch.object(main, "app", mock_app):
        exit_code = main.cli_entrypoint()
    assert exit_code == error.code


def test_cli_entrypoint_handles_unexpected_error() -> None:
    mock_app = MagicMock(side_effect=RuntimeError("boom"))
    with patch.object(main, "app", mock_app):
        exit_code = main.cli_entrypoint()
    assert exit_code == ExitCode.USAGE_ERROR
