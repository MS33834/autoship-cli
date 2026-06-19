"""Local plugin registry and trust level management."""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger("autoship")

DEFAULT_REGISTRY_DIR = Path.home() / ".config" / "autoship"


class TrustLevel(str, Enum):
    """Trust levels for installed plugins."""

    BUILTIN = "builtin"
    VERIFIED = "verified"
    COMMUNITY = "community"
    UNTRUSTED = "untrusted"


class CapabilityManifest(BaseModel):
    """Minimal capability manifest for a plugin."""

    filesystem: str = "read-only"
    network: bool = False
    shell: bool = False
    git: bool = False


class PluginSpec(BaseModel):
    """Metadata for a registered plugin."""

    name: str
    version: str = "0.0.0"
    source: str
    entry_point: str | None = None
    hooks: list[str] = Field(default_factory=list)
    trust_level: TrustLevel = TrustLevel.COMMUNITY
    capabilities: CapabilityManifest = Field(default_factory=CapabilityManifest)
    sha256: str | None = None
    signature: str | None = None
    maintainer: str | None = None
    license: str | None = None


class PluginRegistry:
    """Manage a local JSON registry of installed plugins."""

    def __init__(self, registry_dir: Path | None = None) -> None:
        self.registry_dir = registry_dir or DEFAULT_REGISTRY_DIR
        self.registry_file = self.registry_dir / "registry.json"
        self._plugins: dict[str, PluginSpec] = {}
        self._load()

    def list(self) -> list[PluginSpec]:
        """Return all registered plugins sorted by name."""
        return sorted(self._plugins.values(), key=lambda p: p.name)

    def get(self, name: str) -> PluginSpec | None:
        """Return a plugin by name, or None if not registered."""
        return self._plugins.get(name)

    def add(self, spec: PluginSpec) -> None:
        """Add or update a plugin in the registry."""
        self._plugins[spec.name] = spec
        self._save()

    def remove(self, name: str) -> bool:
        """Remove a plugin from the registry."""
        if name not in self._plugins:
            return False
        del self._plugins[name]
        self._save()
        return True

    def trust(self, name: str, level: TrustLevel) -> bool:
        """Update the trust level of a registered plugin."""
        plugin = self._plugins.get(name)
        if plugin is None:
            return False
        self._plugins[name] = plugin.model_copy(update={"trust_level": level})
        self._save()
        return True

    def _load(self) -> None:
        """Load the registry from disk."""
        if not self.registry_file.exists():
            return
        try:
            data = json.loads(self.registry_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load plugin registry: %s", exc)
            return

        for item in data.get("plugins", []):
            try:
                spec = PluginSpec.model_validate(item)
                self._plugins[spec.name] = spec
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping invalid registry entry: %s", exc)

    def _save(self) -> None:
        """Persist the registry to disk."""
        try:
            self.registry_dir.mkdir(parents=True, exist_ok=True)
            payload = {"plugins": [spec.model_dump(mode="json") for spec in self._plugins.values()]}
            self.registry_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to save plugin registry: %s", exc)
