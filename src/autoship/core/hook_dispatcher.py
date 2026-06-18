"""Plugin hook dispatcher based on pluggy."""

from __future__ import annotations

import logging
from typing import Any

import pluggy

from autoship.core.context import CommandContext
from autoship.exceptions import PluginError
from autoship.hookspec import AutoShipHookSpec

logger = logging.getLogger("autoship")


class HookDispatcher:
    """Manages plugin registration and hook invocation."""

    def __init__(self) -> None:
        self.pm = pluggy.PluginManager("autoship")
        self.pm.add_hookspecs(AutoShipHookSpec)
        self._load_builtin()

    def _load_builtin(self) -> None:
        """Load built-in plugins."""
        from autoship.plugins import defaults

        self.pm.register(defaults.plugin)

    def call(
        self,
        hook_name: str,
        context: CommandContext,
        *,
        fail_fast: bool = True,
        **kwargs: Any,
    ) -> list[Any]:
        """Invoke the named hook for all registered plugins.

        Args:
            hook_name: Name of the hook to invoke.
            context: The current CommandContext.
            fail_fast: If True, a plugin exception aborts the command.
            **kwargs: Additional keyword arguments passed to hook implementations.

        Returns:
            A list of hook return values.
        """
        hook = getattr(self.pm.hook, hook_name)
        results: list[Any] = []
        try:
            results = hook(context=context, **kwargs)
        except Exception as exc:
            logger.warning("Hook %s failed: %s", hook_name, exc)
            if fail_fast:
                raise PluginError(f"Hook {hook_name} failed: {exc}") from exc
        return results
