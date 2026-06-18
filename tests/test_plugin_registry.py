"""Tests for PluginRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest

from autoship.core.plugin_registry import PluginRegistry, PluginSpec, TrustLevel


@pytest.fixture
def registry(tmp_path: Path) -> PluginRegistry:
    """Return a PluginRegistry backed by a temporary directory."""
    return PluginRegistry(registry_dir=tmp_path)


def test_add_and_list(registry: PluginRegistry) -> None:
    spec = PluginSpec(name="my-plugin", source="pypi")
    registry.add(spec)
    plugins = registry.list()
    assert len(plugins) == 1
    assert plugins[0].name == "my-plugin"


def test_get_and_trust(registry: PluginRegistry) -> None:
    registry.add(PluginSpec(name="a", source="local"))
    assert registry.trust("a", TrustLevel.VERIFIED) is True
    plugin = registry.get("a")
    assert plugin is not None
    assert plugin.trust_level == TrustLevel.VERIFIED


def test_remove(registry: PluginRegistry) -> None:
    registry.add(PluginSpec(name="b", source="local"))
    assert registry.remove("b") is True
    assert registry.remove("b") is False


def test_persistence(tmp_path: Path) -> None:
    registry = PluginRegistry(registry_dir=tmp_path)
    registry.add(PluginSpec(name="persist", source="git"))

    registry2 = PluginRegistry(registry_dir=tmp_path)
    assert registry2.get("persist") is not None
