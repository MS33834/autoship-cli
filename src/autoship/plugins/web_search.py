"""Official web-search plugin for AutoShip-CLI.

When enabled, this plugin searches the web for context about a verification
failure and includes the top results in the AI fix prompt. Web search is
disabled by default and must be explicitly turned on via configuration.
"""

from __future__ import annotations

import logging

from autoship.adapters.model_gateway import ChatMessage
from autoship.adapters.web_search import WebSearchAdapter, WebSearchResult, format_results
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.core.model_router import ModelRouter
from autoship.exceptions import ModelGatewayError, VerifyError
from autoship.hookspec import hookimpl

logger = logging.getLogger("autoship")


class WebSearchPlugin:
    """Provide web-augmented fix suggestions via ``on_error``."""

    @hookimpl
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        """Search the web for error context and return an augmented fix suggestion."""
        if not context.extras.get("fix"):
            return None

        config = context.config.web_search
        if not config.enabled:
            return None

        query = _build_query(error)
        if not query:
            return None

        adapter = WebSearchAdapter(timeout=config.timeout)
        try:
            results = adapter.search(query, max_results=config.max_results)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Web search failed: %s", exc)
            return None

        if not results:
            return None

        return _suggest_with_search(context, error, results)


def _build_query(error: Exception) -> str:
    """Create a concise search query from an error."""
    if isinstance(error, VerifyError):
        command = error.details.get("command", "")
        stderr = error.details.get("stderr", "")
        return f"{command} {stderr[:200]}".strip()
    return str(error)[:200]


def _suggest_with_search(
    context: CommandContext,
    error: Exception,
    results: list[WebSearchResult],
) -> FixSuggestion | None:
    """Ask the model to suggest a fix using web search results as context."""
    router = ModelRouter(context.config)
    search_context = format_results(results)
    prompt = (
        "The following verification command failed. Use the web search results "
        "below to suggest a concise fix in one or two sentences.\n\n"
        f"Error: {error}\n\n"
        f"Web search results:\n{search_context}"
    )

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

    return FixSuggestion(description=suggestion.strip())


plugin = WebSearchPlugin()
