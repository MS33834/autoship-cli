"""Remote plugin registry client with local caching and offline fallback."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, cast

import httpx

from autoship.core.metrics import get_registry
from autoship.models.config import AppConfig, RegistryConfig

logger = logging.getLogger("autoship")

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "autoship"
DEFAULT_CACHE_FILE = DEFAULT_CACHE_DIR / "registry.json"


class RegistryClient:
    """Fetch the plugin registry index from a remote URL with local cache.

    The client follows this resolution order:

    1. If ``use_cache`` is enabled and the cache is fresh, return it.
    2. Fetch from the configured remote ``url`` and update the cache.
    3. If the remote is unreachable, return a stale cache if present.
    4. Fall back to the bundled index shipped with the CLI.
    """

    def __init__(
        self,
        config: RegistryConfig | None = None,
        cache_file: Path | None = None,
    ) -> None:
        self.config = config or RegistryConfig()
        self.cache_file = cache_file or DEFAULT_CACHE_FILE

    def _cache_is_fresh(self) -> bool:
        if not self.cache_file.exists():
            return False
        if not self.config.cache_enabled:
            return False
        try:
            mtime = self.cache_file.stat().st_mtime
        except OSError:
            return False
        return (time.time() - mtime) < self.config.cache_ttl_seconds

    def _read_cache(self) -> dict[str, Any] | None:
        if not self.cache_file.exists():
            return None
        try:
            raw = self.cache_file.read_text(encoding="utf-8")
            return cast(dict[str, Any], json.loads(raw))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read registry cache: %s", exc)
            return None

    def _write_cache(self, data: dict[str, Any]) -> None:
        if not self.config.cache_enabled:
            return
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to write registry cache: %s", exc)

    def _fetch_remote(self) -> dict[str, Any] | None:
        registry = get_registry()
        start = time.perf_counter()
        try:
            response = httpx.get(str(self.config.url), timeout=10.0)
            response.raise_for_status()
            data = cast(dict[str, Any], response.json())
            self._write_cache(data)
            registry.inc("registry_sync_success", description="Successful registry syncs")
            return data
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            logger.warning("Failed to fetch remote registry index: %s", exc)
            registry.inc("registry_sync_errors", description="Registry sync errors")
            return None
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            registry.record(
                "registry_sync_latency_ms", elapsed_ms, description="Registry sync latency"
            )

    def _bundled_index(self) -> dict[str, Any]:
        package_root = Path(__file__).resolve().parents[1]
        bundled = package_root / "registry" / "plugins.json"
        if bundled.exists():
            try:
                return cast(dict[str, Any], json.loads(bundled.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Failed to load bundled registry index: %s", exc)
        return {"version": 1, "plugins": []}

    def get(self, *, no_cache: bool = False) -> dict[str, Any]:
        """Return the registry index, using cache and fallbacks as needed."""
        if not no_cache and self._cache_is_fresh():
            cached = self._read_cache()
            if cached is not None:
                return cached

        remote = self._fetch_remote()
        if remote is not None:
            return remote

        cached = self._read_cache()
        if cached is not None:
            logger.info("Using stale registry cache because remote is unavailable")
            return cached

        return self._bundled_index()

    def clear_cache(self) -> None:
        """Remove the local registry cache file."""
        try:
            self.cache_file.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Failed to clear registry cache: %s", exc)

    def fetch_index(self, *, force: bool = False) -> dict[str, Any] | None:
        """Fetch the registry index from the remote URL.

        This bypasses the freshness check and always contacts the remote.
        If ``force`` is True, the local cache is cleared first so a stale
        cached index cannot be returned.
        """
        if force:
            self.clear_cache()
        return self._fetch_remote()


def get_registry_client(config: AppConfig | None = None) -> RegistryClient:
    """Factory for the default registry client."""
    registry_config = config.registry if config else RegistryConfig()
    return RegistryClient(config=registry_config)
