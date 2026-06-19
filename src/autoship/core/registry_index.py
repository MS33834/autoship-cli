"""Official plugin registry index loader and search."""

from __future__ import annotations

from typing import Any, cast

from autoship.core.registry_client import RegistryClient
from autoship.models.config import AppConfig


class RegistryIndex:
    """Load and query the official plugin registry index."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.client = RegistryClient(config.registry if config else None)
        self._data: dict[str, Any] | None = None

    def load(self, *, no_cache: bool = False) -> dict[str, Any]:
        """Load the registry index via the caching client."""
        if self._data is not None and not no_cache:
            return self._data

        data = self.client.get(no_cache=no_cache)
        self._data = data
        return data

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
