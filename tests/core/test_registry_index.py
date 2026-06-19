"""Tests for the official plugin registry index."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoship.core.registry_index import RegistryIndex


@pytest.fixture
def sample_index(tmp_path: Path) -> Path:
    data = {
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
    path = tmp_path / "registry" / "plugins.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_registry_index_loads_local_file(sample_index: Path) -> None:
    index = RegistryIndex()
    index._local_path = lambda: sample_index  # type: ignore[method-assign]
    plugins = index.list_plugins()
    assert len(plugins) == 2


def test_registry_index_search_by_name(sample_index: Path) -> None:
    index = RegistryIndex()
    index._local_path = lambda: sample_index  # type: ignore[method-assign]
    results = index.search("docker")
    assert len(results) == 1
    assert results[0]["name"] == "docker-ship"


def test_registry_index_search_by_description(sample_index: Path) -> None:
    index = RegistryIndex()
    index._local_path = lambda: sample_index  # type: ignore[method-assign]
    results = index.search("scanning")
    assert len(results) == 1
    assert results[0]["name"] == "security-scan"


def test_registry_index_get_by_name(sample_index: Path) -> None:
    index = RegistryIndex()
    index._local_path = lambda: sample_index  # type: ignore[method-assign]
    plugin = index.get("security-scan")
    assert plugin is not None
    assert plugin["package"] == "autoship"


def test_registry_index_get_missing(sample_index: Path) -> None:
    index = RegistryIndex()
    index._local_path = lambda: sample_index  # type: ignore[method-assign]
    assert index.get("not-found") is None


def test_registry_index_empty_when_no_file(tmp_path: Path) -> None:
    index = RegistryIndex()
    index._local_path = lambda: tmp_path / "registry" / "plugins.json"  # type: ignore[method-assign]
    plugins = index.list_plugins()
    assert plugins == []
