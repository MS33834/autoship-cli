"""Tests for the caching registry client."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import httpx

from autoship.core.registry_client import RegistryClient
from autoship.models.config import RegistryConfig


def test_returns_fresh_cache(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    cached_data = {"version": 2, "plugins": [{"name": "cached"}]}
    cache.write_text(json.dumps(cached_data), encoding="utf-8")

    client = RegistryClient(cache_file=cache)
    result = client.get()
    assert result == cached_data


def test_fetches_remote_and_caches(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    remote_data = {"version": 2, "plugins": [{"name": "remote"}]}

    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(cache_file=cache)
        result = client.get()

    assert result == remote_data
    assert cache.exists()
    assert json.loads(cache.read_text(encoding="utf-8")) == remote_data


def test_falls_back_to_stale_cache_on_remote_failure(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    stale_data = {"version": 2, "plugins": [{"name": "stale"}]}
    cache.write_text(json.dumps(stale_data), encoding="utf-8")

    config = RegistryConfig(cache_enabled=True, cache_ttl_seconds=0)
    with patch("autoship.core.registry_client.httpx.get", side_effect=httpx.ConnectError("offline")):
        client = RegistryClient(config=config, cache_file=cache)
        result = client.get()

    assert result == stale_data


def test_no_cache_option_bypasses_cache(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    cached_data = {"version": 2, "plugins": [{"name": "cached"}]}
    remote_data = {"version": 2, "plugins": [{"name": "fresh"}]}
    cache.write_text(json.dumps(cached_data), encoding="utf-8")

    config = RegistryConfig(cache_enabled=True, cache_ttl_seconds=3600)
    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(config=config, cache_file=cache)
        result = client.get(no_cache=True)

    assert result == remote_data


def test_clear_cache_removes_file(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    cache.write_text("{}", encoding="utf-8")
    client = RegistryClient(cache_file=cache)
    client.clear_cache()
    assert not cache.exists()
