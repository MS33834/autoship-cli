"""Tests for the caching registry client."""

from __future__ import annotations

import base64
import hashlib
import json
import stat
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autoship.core.registry_client import RegistryClient
from autoship.exceptions import RegistryError
from autoship.models.config import RegistryConfig


def _canonical_payload(data: dict[str, Any]) -> bytes:
    """Return the canonical bytes used for signing and hashing."""
    stripped = {k: v for k, v in data.items() if k not in ("sha256", "signature")}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign_index(data: dict[str, Any]) -> tuple[bytes, bytes]:
    """Return (public_key_bytes, signature_bytes) for the given index data."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    signature = private_key.sign(_canonical_payload(data))
    return public_key.public_bytes_raw(), signature


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
    with patch(
        "autoship.core.registry_client.httpx.get", side_effect=httpx.ConnectError("offline")
    ):
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


def test_valid_signed_index_is_cached(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    remote_data = {"version": 2, "plugins": [{"name": "remote"}]}
    public_key, signature = _sign_index(remote_data)
    remote_data["sha256"] = hashlib.sha256(_canonical_payload(remote_data)).hexdigest()
    remote_data["signature"] = base64.b64encode(signature).decode("ascii")

    config = RegistryConfig(public_key=base64.b64encode(public_key).decode("ascii"))
    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(config=config, cache_file=cache)
        result = client.get()

    assert result["plugins"] == [{"name": "remote"}]
    assert cache.exists()
    assert json.loads(cache.read_text(encoding="utf-8"))["signature"] == remote_data["signature"]


def test_tampered_signature_raises_and_does_not_cache(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    remote_data = {"version": 2, "plugins": [{"name": "remote"}]}
    public_key, signature = _sign_index(remote_data)
    remote_data["sha256"] = hashlib.sha256(_canonical_payload(remote_data)).hexdigest()
    remote_data["signature"] = base64.b64encode(signature).decode("ascii")

    # Tamper with the payload after signing.
    remote_data["plugins"][0]["name"] = "evil"

    config = RegistryConfig(public_key=base64.b64encode(public_key).decode("ascii"))
    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(config=config, cache_file=cache)

        with pytest.raises(RegistryError):
            client.get()

    assert not cache.exists()


def test_tampered_cache_is_rejected(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    remote_data = {"version": 2, "plugins": [{"name": "remote"}]}
    public_key, signature = _sign_index(remote_data)
    remote_data["sha256"] = hashlib.sha256(_canonical_payload(remote_data)).hexdigest()
    remote_data["signature"] = base64.b64encode(signature).decode("ascii")

    # Write a cache file that has a valid structure but does not match the signature.
    tampered = dict(remote_data)
    tampered["plugins"] = [{"name": "evil"}]
    cache.write_text(json.dumps(tampered), encoding="utf-8")

    config = RegistryConfig(
        public_key=base64.b64encode(public_key).decode("ascii"), cache_ttl_seconds=3600
    )
    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(config=config, cache_file=cache)
        result = client.get()

    assert result["plugins"] == [{"name": "remote"}]


def test_missing_signature_with_public_key_raises(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    remote_data = {"version": 2, "plugins": [{"name": "remote"}]}
    public_key, _signature = _sign_index(remote_data)

    config = RegistryConfig(public_key=base64.b64encode(public_key).decode("ascii"))
    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(config=config, cache_file=cache)
        with pytest.raises(RegistryError):
            client.get()


def test_invalid_sha256_raises(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    remote_data = {"version": 2, "plugins": [{"name": "remote"}]}
    public_key, signature = _sign_index(remote_data)
    remote_data["sha256"] = "0" * 64
    remote_data["signature"] = base64.b64encode(signature).decode("ascii")

    config = RegistryConfig(public_key=base64.b64encode(public_key).decode("ascii"))
    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(config=config, cache_file=cache)
        with pytest.raises(RegistryError):
            client.get()


def test_registry_cache_has_restrictive_permissions(tmp_path: Path) -> None:
    """Registry cache directory and file are only owner-readable/writable."""
    cache = tmp_path / "registry.json"
    remote_data = {"version": 2, "plugins": [{"name": "remote"}]}

    with patch("autoship.core.registry_client.httpx.get") as mock_get:
        mock_get.return_value.json.return_value = remote_data
        mock_get.return_value.raise_for_status = lambda: None
        client = RegistryClient(cache_file=cache)
        client.get()

    assert cache.parent.exists()
    assert stat.S_IMODE(cache.parent.stat().st_mode) == 0o700
    assert cache.exists()
    assert stat.S_IMODE(cache.stat().st_mode) == 0o600
