"""Tests for registry analytics commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from autoship.cli.main import app

runner = CliRunner()


def test_registry_dashboard_shows_metrics() -> None:
    plugins = [
        {
            "name": "a",
            "trust_level": "verified",
            "categories": ["security"],
            "downloads": 100,
            "rating": {"score": 4.5, "count": 10},
            "publisher": {"id": "alice", "verified": True, "url": ""},
        },
        {
            "name": "b",
            "trust_level": "community",
            "categories": ["productivity"],
            "downloads": 50,
            "rating": {"score": 3.0, "count": 2},
        },
    ]
    with patch("autoship.cli.commands.registry.RegistryIndex") as mock_index:
        mock_index.return_value.list_plugins.return_value = plugins
        result = runner.invoke(app, ["registry", "dashboard"])
    assert result.exit_code == 0
    assert "Total plugins: 2" in result.output
    assert "verified" in result.output
    assert "community" in result.output
    assert "a" in result.output
    assert "b" in result.output


def test_registry_dashboard_empty() -> None:
    with patch("autoship.cli.commands.registry.RegistryIndex") as mock_index:
        mock_index.return_value.list_plugins.return_value = []
        result = runner.invoke(app, ["registry", "dashboard"])
    assert result.exit_code == 0
    assert "No plugins found" in result.output


def test_registry_sync_writes_files(tmp_path: Path) -> None:
    output = tmp_path / "registry" / "plugins.json"
    bundled = tmp_path / "bundled" / "plugins.json"
    remote_data = {
        "version": 2,
        "plugins": [
            {"name": "alpha", "version": "1.0.0"},
            {"name": "beta", "version": "2.0.0"},
        ],
    }

    with (
        patch(
            "autoship.cli.commands.registry.RegistryClient.fetch_index",
            return_value=remote_data,
        ) as mock_fetch,
        patch("autoship.cli.commands.registry.BUNDLED_REGISTRY_PATH", bundled),
    ):
        result = runner.invoke(app, ["registry", "sync", "--output", str(output)])

    assert result.exit_code == 0
    mock_fetch.assert_called_once_with(force=False)
    assert output.exists()
    assert bundled.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == remote_data
    assert json.loads(bundled.read_text(encoding="utf-8")) == remote_data
    assert "Synced" in result.output


def test_registry_sync_dry_run_does_not_write(tmp_path: Path) -> None:
    output = tmp_path / "registry" / "plugins.json"
    bundled = tmp_path / "bundled" / "plugins.json"
    remote_data = {
        "version": 2,
        "plugins": [{"name": "alpha", "version": "1.0.0"}],
    }

    with (
        patch(
            "autoship.cli.commands.registry.RegistryClient.fetch_index",
            return_value=remote_data,
        ),
        patch("autoship.cli.commands.registry.BUNDLED_REGISTRY_PATH", bundled),
    ):
        result = runner.invoke(app, ["registry", "sync", "--dry-run", "--output", str(output)])

    assert result.exit_code == 0
    assert not output.exists()
    assert not bundled.exists()
    assert "[dry-run]" in result.output


def test_registry_sync_remote_failure_exits_nonzero() -> None:
    with patch(
        "autoship.cli.commands.registry.RegistryClient.fetch_index",
        return_value=None,
    ):
        result = runner.invoke(app, ["registry", "sync"])
    assert result.exit_code == 1
    assert "Failed to sync" in result.output


def test_registry_sync_force_clears_cache(tmp_path: Path) -> None:
    output = tmp_path / "registry" / "plugins.json"
    bundled = tmp_path / "bundled" / "plugins.json"
    remote_data = {"version": 2, "plugins": []}

    with (
        patch(
            "autoship.cli.commands.registry.RegistryClient.fetch_index",
            return_value=remote_data,
        ) as mock_fetch,
        patch("autoship.cli.commands.registry.BUNDLED_REGISTRY_PATH", bundled),
    ):
        result = runner.invoke(app, ["registry", "sync", "--force", "--output", str(output)])

    assert result.exit_code == 0
    mock_fetch.assert_called_once_with(force=True)
