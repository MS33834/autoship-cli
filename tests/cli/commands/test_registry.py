"""Tests for registry analytics commands."""

from __future__ import annotations

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
