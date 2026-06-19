"""Tests for the plugin CLI command."""

from __future__ import annotations

from unittest.mock import patch

from packaging.version import parse as parse_version
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


def test_plugin_search_shows_indexed_plugins() -> None:
    result = runner.invoke(app, ["plugin", "search"])
    assert result.exit_code == 0
    assert "security-scan" in result.output


def test_plugin_search_filters_by_keyword() -> None:
    result = runner.invoke(app, ["plugin", "search", "docker"])
    assert result.exit_code == 0
    assert "docker-ship" in result.output
    assert "web-search" not in result.output


def test_plugin_install_dry_run() -> None:
    result = runner.invoke(app, ["plugin", "install", "my-plugin", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run] Would install my-plugin" in result.output


def test_plugin_install_from_registry_dry_run() -> None:
    result = runner.invoke(app, ["plugin", "install", "security-scan", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run] Would install security-scan" in result.output
    assert "autoship" in result.output


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


def test_plugin_install_community_requires_confirmation() -> None:
    result = runner.invoke(app, ["plugin", "install", "jira-link"], input="n\n")
    assert result.exit_code == 0
    assert "community plugin" in result.output


def test_plugin_install_untrusted_requires_confirmation() -> None:
    result = runner.invoke(
        app, ["plugin", "install", "./local-plugin", "--trust", "untrusted"], input="n\n"
    )
    assert result.exit_code == 0
    assert "untrusted" in result.output


def test_plugin_install_skip_trust_check() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = None
        result = runner.invoke(
            app, ["plugin", "install", "jira-link", "--skip-trust-check", "--yes"]
        )
    assert result.exit_code == 0
    assert "Installed plugin: jira-link" in result.output


def test_plugin_install_verified_without_signature_warns() -> None:
    with patch("autoship.cli.commands.plugin.RegistryIndex") as mock_index:
        mock_index.return_value.get.return_value = {
            "name": "verified-no-sig",
            "package": "verified-no-sig",
            "version": "1.0.0",
            "trust_level": "verified",
            "entry_point": "verified_no_sig.plugin:Plugin",
            "hooks": [],
        }
        result = runner.invoke(app, ["plugin", "install", "verified-no-sig"], input="n\n")
    assert result.exit_code == 0
    assert "no checksum or signature" in result.output


def test_plugin_update_requires_name_or_all() -> None:
    result = runner.invoke(app, ["plugin", "update"])
    assert result.exit_code != 0
    assert result.exception is not None
    assert "name or use --all" in str(result.exception)


def test_plugin_update_no_updates() -> None:
    plugins = [
        PluginSpec(name="a", version="1.0.0", source="pkg-a", trust_level=TrustLevel.VERIFIED),
    ]
    with (
        patch("autoship.cli.commands.plugin.PluginRegistry") as mock_reg,
        patch("autoship.cli.commands.plugin.RegistryIndex") as mock_index,
        patch("autoship.cli.commands.plugin._installed_version", return_value=parse_version("1.0.0")),
    ):
        mock_reg.return_value.list.return_value = plugins
        mock_reg.return_value.get.return_value = plugins[0]
        mock_index.return_value.get.return_value = {"version": "1.0.0"}
        result = runner.invoke(app, ["plugin", "update", "--all"])
    assert result.exit_code == 0
    assert "No plugin updates" in result.output


def test_plugin_update_dry_run() -> None:
    plugins = [
        PluginSpec(name="a", version="1.0.0", source="pkg-a", trust_level=TrustLevel.VERIFIED),
    ]
    with (
        patch("autoship.cli.commands.plugin.PluginRegistry") as mock_reg,
        patch("autoship.cli.commands.plugin.RegistryIndex") as mock_index,
        patch("autoship.cli.commands.plugin._installed_version", return_value=parse_version("1.0.0")),
    ):
        mock_reg.return_value.list.return_value = plugins
        mock_reg.return_value.get.return_value = plugins[0]
        mock_index.return_value.get.return_value = {"version": "2.0.0"}
        result = runner.invoke(app, ["plugin", "update", "--all", "--dry-run"])
    assert result.exit_code == 0
    assert "Would update a" in result.output


def test_plugin_update_skips_builtin() -> None:
    plugins = [
        PluginSpec(name="security-scan", version="1.0.0", source="autoship", trust_level=TrustLevel.BUILTIN),
    ]
    with (
        patch("autoship.cli.commands.plugin.PluginRegistry") as mock_reg,
        patch("autoship.cli.commands.plugin.RegistryIndex") as mock_index,
        patch("autoship.cli.commands.plugin._installed_version", return_value=parse_version("1.0.0")),
    ):
        mock_reg.return_value.list.return_value = plugins
        mock_index.return_value.get.return_value = {"version": "2.0.0"}
        result = runner.invoke(app, ["plugin", "update", "--all"])
    assert result.exit_code == 0
    assert "built-in" in result.output


def test_plugin_update_upgrades_plugin() -> None:
    plugins = [
        PluginSpec(name="a", version="1.0.0", source="pkg-a", trust_level=TrustLevel.VERIFIED),
    ]
    with (
        patch("autoship.cli.commands.plugin.PluginRegistry") as mock_reg,
        patch("autoship.cli.commands.plugin.RegistryIndex") as mock_index,
        patch("autoship.cli.commands.plugin._installed_version", return_value=parse_version("1.0.0")),
        patch("subprocess.run") as mock_run,
    ):
        mock_reg.return_value.list.return_value = plugins
        mock_reg.return_value.get.return_value = plugins[0]
        mock_index.return_value.get.return_value = {"version": "2.0.0"}
        result = runner.invoke(app, ["plugin", "update", "--all", "--yes"])
    assert result.exit_code == 0
    assert "Updated plugin: a -> 2.0.0" in result.output
    mock_run.assert_called_once()


def test_plugin_rate_records_rating() -> None:
    with (
        patch("autoship.cli.commands.plugin.PluginRegistry") as mock_reg,
        patch("autoship.cli.commands.plugin.PluginStats") as mock_stats,
    ):
        mock_reg.return_value.get.return_value = PluginSpec(name="a", source="pypi")
        result = runner.invoke(app, ["plugin", "rate", "a", "4.5"])
    assert result.exit_code == 0
    assert "Rated a: 4.5" in result.output
    mock_stats.return_value.record_rate.assert_called_once_with("a", 4.5)


def test_plugin_rate_rejects_out_of_range() -> None:
    with patch("autoship.cli.commands.plugin.PluginRegistry") as mock_reg:
        mock_reg.return_value.get.return_value = PluginSpec(name="a", source="pypi")
        result = runner.invoke(app, ["plugin", "rate", "a", "6"])
    assert result.exit_code != 0


def test_plugin_stats_shows_summary() -> None:
    with patch("autoship.cli.commands.plugin.PluginStats") as mock_stats:
        mock_stats.return_value.summary.return_value = {
            "a": {
                "installs": 2,
                "uninstalls": 1,
                "rating": {"score": 4.5, "count": 2},
            }
        }
        result = runner.invoke(app, ["plugin", "stats"])
    assert result.exit_code == 0
    assert "a" in result.output
    assert "4.5 (2)" in result.output
