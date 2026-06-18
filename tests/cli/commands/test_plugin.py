"""Tests for the plugin CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from autoship.cli.main import app
from autoship.core.plugin_registry import PluginSpec, TrustLevel

runner = CliRunner()


def test_plugin_list_empty() -> None:
    with patch("autoship.cli.commands.plugin.PluginRegistry") as mock_cls:
        mock_cls.return_value.list.return_value = []
        result = runner.invoke(app, ["plugin", "list"])
    assert result.exit_code == 0
    assert "No plugins registered" in result.output


def test_plugin_list_shows_plugins() -> None:
    plugins = [
        PluginSpec(name="a", version="1.0.0", source="pypi", trust_level=TrustLevel.VERIFIED),
        PluginSpec(name="b", version="2.0.0", source="git", trust_level=TrustLevel.COMMUNITY),
    ]
    with patch("autoship.cli.commands.plugin.PluginRegistry") as mock_cls:
        mock_cls.return_value.list.return_value = plugins
        result = runner.invoke(app, ["plugin", "list"])
    assert result.exit_code == 0
    assert "a" in result.output
    assert "verified" in result.output


def test_plugin_trust() -> None:
    with patch("autoship.cli.commands.plugin.PluginRegistry") as mock_cls:
        mock_cls.return_value.trust.return_value = True
        result = runner.invoke(app, ["plugin", "trust", "a", "verified"])
    assert result.exit_code == 0
    assert "Set trust level of a to verified" in result.output


def test_plugin_install_dry_run() -> None:
    result = runner.invoke(app, ["plugin", "install", "my-plugin", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run] Would install my-plugin" in result.output


def test_plugin_uninstall_dry_run() -> None:
    with patch("autoship.cli.commands.plugin.PluginRegistry") as mock_cls:
        mock_cls.return_value.get.return_value = PluginSpec(name="x", source="pypi")
        result = runner.invoke(app, ["plugin", "uninstall", "x", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run] Would uninstall x" in result.output


def test_plugin_install_pip_failure() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError("no pip")):
        result = runner.invoke(app, ["plugin", "install", "bad", "--yes"])
    assert result.exit_code != 0
    assert result.exception is not None
    assert "Failed to install plugin" in str(result.exception)
