"""Default built-in plugin implementations."""

from __future__ import annotations

import subprocess

from autoship.adapters.model_gateway import ChatMessage
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.core.model_router import ModelRouter
from autoship.exceptions import ModelGatewayError, VerifyError
from autoship.hookspec import hookimpl


class BuiltinPlugins:
    """Built-in plugins providing default AI-assisted behaviours."""

    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        """Run security scans by delegating to the security-scan plugin."""
        from autoship.plugins import security_scan

        security_scan.plugin.pre_commit(context)

    @hookimpl
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        """Suggest a fix when a command fails and the user requested --fix."""
        if not context.extras.get("fix"):
            return None

        stdout, stderr = "", ""
        if isinstance(error, VerifyError):
            stdout = error.details.get("stdout", "")
            stderr = error.details.get("stderr", "")
        elif isinstance(error, subprocess.CalledProcessError):
            stdout = error.stdout or ""
            stderr = error.stderr or ""

        command = context.extras.get("verify_command", "")
        prompt = (
            "The following verification command failed. "
            "Suggest a concise fix in one or two sentences. "
            "If you can provide a unified diff patch, include it after the description "
            "under a line starting with '```diff'.\n\n"
            f"Command: {command}\n\n"
            f"stdout:\n{stdout[-4000:]}\n\n"
            f"stderr:\n{stderr[-4000:]}"
        )

        router = ModelRouter(context.config)
        try:
            suggestion = router.chat(
                [
                    ChatMessage(role="system", content="You are a helpful debugging assistant."),
                    ChatMessage(role="user", content=prompt),
                ],
                "verify-fix",
            )
        except ModelGatewayError:
            return None

        return _parse_suggestion(suggestion)


def _parse_suggestion(text: str) -> FixSuggestion:
    """Split a model response into description and optional diff patch."""
    if "```diff" in text:
        description, _, patch_block = text.partition("```diff")
        patch = patch_block.replace("```", "").strip()
        return FixSuggestion(description=description.strip(), patch=patch)
    return FixSuggestion(description=text.strip())


plugin = BuiltinPlugins()
