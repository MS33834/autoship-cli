"""Tests for autoship-community-echo."""

from __future__ import annotations

from community_echo.plugin import CommunityEchoPlugin


def test_plugin_can_be_instantiated() -> None:
    plugin = CommunityEchoPlugin()
    assert plugin is not None
