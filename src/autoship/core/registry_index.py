"""Official plugin registry index loader and search."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

import httpx

from autoship.models.config import AppConfig

logger = logging.getLogger("autoship")

DEFAULT_INDEX_URL = "https://raw.githubusercontent.com/autoship-cli/autoship-cli/main/registry/plugins.json"


class RegistryIndex:
    """Load and query the official plugin registry index."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config
        self._data: dict[str, Any] | None = None

    def _local_path(self) -> Path:
        """Return the bundled registry index path."""
        package_root = Path(__file__).resolve().parents[1]
        return package_root / "registry" / "plugins.json"

    def load(self) -> dict[str, Any]:
        """Load the registry index from local bundle or remote fallback."""
        if self._data is not None:
            return self._data

        local_path = self._local_path()
        if local_path.exists():
            try:
                local_data = cast(dict[str, Any], json.loads(local_path.read_text(encoding="utf-8")))
                self._data = local_data
                return local_data
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Failed to load local registry index: %s", exc)

        try:
            response = httpx.get(DEFAULT_INDEX_URL, timeout=10.0)
            response.raise_for_status()
            remote_data = cast(dict[str, Any], response.json())
            self._data = remote_data
            return remote_data
        except httpx.HTTPError as exc:
            logger.warning("Failed to fetch remote registry index: %s", exc)

        fallback: dict[str, Any] = {"version": 1, "plugins": []}
        self._data = fallback
        return fallback

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return all plugins in the index."""
        return cast(list[dict[str, Any]], self.load().get("plugins", []))

    def search(self, keyword: str | None = None) -> list[dict[str, Any]]:
        """Search plugins by keyword in name or description."""
        plugins = self.list_plugins()
        if not keyword:
            return plugins
        keyword_lower = keyword.lower()
        return [
            plugin
            for plugin in plugins
            if keyword_lower in plugin.get("name", "").lower()
            or keyword_lower in plugin.get("description", "").lower()
        ]

    def get(self, name: str) -> dict[str, Any] | None:
        """Return a plugin by exact name."""
        for plugin in self.list_plugins():
            if plugin.get("name") == name:
                return plugin
        return None
