"""Tests for the official plugin registry index."""

from __future__ import annotations

from unittest.mock import patch

from autoship.core.registry_index import RegistryIndex

SAMPLE_REGISTRY = {
    "version": 1,
    "plugins": [
        {
            "name": "security-scan",
            "package": "autoship",
            "version": "0.2.0",
            "description": "Security scanning plugin.",
            "trust_level": "builtin",
        },
        {
            "name": "docker-ship",
            "package": "autoship",
            "version": "0.2.0",
            "description": "Docker build and push plugin.",
            "trust_level": "builtin",
        },
    ],
}


def test_registry_index_loads_plugins() -> None:
    with patch("autoship.core.registry_index.RegistryClient") as mock_client:
        mock_client.return_value.get.return_value = SAMPLE_REGISTRY
        index = RegistryIndex()
        plugins = index.list_plugins()
    assert len(plugins) == 2


def test_registry_index_search_by_name() -> None:
    with patch("autoship.core.registry_index.RegistryClient") as mock_client:
        mock_client.return_value.get.return_value = SAMPLE_REGISTRY
        index = RegistryIndex()
        results = index.search("docker")
    assert len(results) == 1
    assert results[0]["name"] == "docker-ship"


def test_registry_index_search_by_description() -> None:
    with patch("autoship.core.registry_index.RegistryClient") as mock_client:
        mock_client.return_value.get.return_value = SAMPLE_REGISTRY
        index = RegistryIndex()
        results = index.search("scanning")
    assert len(results) == 1
    assert results[0]["name"] == "security-scan"


def test_registry_index_get_by_name() -> None:
    with patch("autoship.core.registry_index.RegistryClient") as mock_client:
        mock_client.return_value.get.return_value = SAMPLE_REGISTRY
        index = RegistryIndex()
        plugin = index.get("security-scan")
    assert plugin is not None
    assert plugin["package"] == "autoship"


def test_registry_index_get_missing() -> None:
    with patch("autoship.core.registry_index.RegistryClient") as mock_client:
        mock_client.return_value.get.return_value = SAMPLE_REGISTRY
        index = RegistryIndex()
    assert index.get("not-found") is None


def test_registry_index_empty() -> None:
    with patch("autoship.core.registry_index.RegistryClient") as mock_client:
        mock_client.return_value.get.return_value = {"version": 1, "plugins": []}
        index = RegistryIndex()
        plugins = index.list_plugins()
    assert plugins == []
