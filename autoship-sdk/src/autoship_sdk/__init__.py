"""AutoShip plugin development SDK.

This package provides helpers, base classes, and testing utilities for building
AutoShip plugins.
"""

from __future__ import annotations

from autoship_sdk.plugin import Plugin, hook
from autoship_sdk.templates import TemplateError, create_plugin
from autoship_sdk.testing import PluginTestHarness

__all__ = ["Plugin", "hook", "PluginTestHarness", "create_plugin", "TemplateError"]
