"""Tests for the built-in web-search plugin."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.exceptions import VerifyError
from autoship.models.config import AppConfig, WebSearchConfig, WebSearchProvider
from autoship.plugins import web_search


@pytest.fixture
def web_context(app_config: AppConfig) -> CommandContext:
    """Return a CommandContext with web search enabled."""
    app_config.web_search = WebSearchConfig(enabled=True, max_results=2)
    return CommandContext(
        command="verify",
        project_root=app_config.project_root,
        config=app_config,
        extras={"fix": True, "verify_command": "pytest"},
    )


def test_web_search_disabled_by_default(app_config: AppConfig) -> None:
    ctx = CommandContext(
        command="verify",
        project_root=app_config.project_root,
        config=app_config,
        extras={"fix": True},
    )
    assert web_search.plugin.on_error(ctx, VerifyError("fail")) is None


def test_web_search_returns_suggestion(web_context: CommandContext) -> None:
    results = [
        MagicMock(title="Fix 1", url="https://example.com/1", snippet="do this"),
    ]

    with (
        patch.object(web_search.WebSearchAdapter, "search", return_value=results),
        patch.object(web_search, "ModelRouter") as mock_router,
    ):
        mock_router.return_value.chat.return_value = "Try updating pytest."
        suggestion = web_search.plugin.on_error(
            web_context,
            VerifyError("failed", details={"command": "pytest", "stderr": "error"}),
        )

    assert isinstance(suggestion, FixSuggestion)
    assert "Try updating pytest" in suggestion.description


def test_web_search_no_results_returns_none(web_context: CommandContext) -> None:
    with patch.object(web_search.WebSearchAdapter, "search", return_value=[]):
        assert web_search.plugin.on_error(web_context, VerifyError("fail")) is None


def test_web_search_without_fix_flag_returns_none(web_context: CommandContext) -> None:
    web_context.extras["fix"] = False
    assert web_search.plugin.on_error(web_context, VerifyError("fail")) is None


def test_web_search_default_provider_is_duckduckgo(app_config: AppConfig) -> None:
    assert app_config.web_search.provider == WebSearchProvider.DUCKDUCKGO


def test_web_search_routes_to_duckduckgo(web_context: CommandContext) -> None:
    results = [
        MagicMock(title="Fix 1", url="https://example.com/1", snippet="do this"),
    ]

    with (
        patch.object(web_search.WebSearchAdapter, "search", return_value=results) as mock_search,
        patch.object(web_search, "ModelRouter") as mock_router,
    ):
        mock_router.return_value.chat.return_value = "Try updating pytest."
        suggestion = web_search.plugin.on_error(
            web_context,
            VerifyError("failed", details={"command": "pytest", "stderr": "error"}),
        )

    assert isinstance(suggestion, FixSuggestion)
    assert "Try updating pytest" in suggestion.description
    mock_search.assert_called_once()


def test_web_search_unimplemented_provider_raises(web_context: CommandContext) -> None:
    web_context.config.web_search.provider = WebSearchProvider.BRAVE
    with pytest.raises(NotImplementedError, match="brave"):
        web_search.plugin.on_error(
            web_context,
            VerifyError("failed", details={"command": "pytest", "stderr": "error"}),
        )


def test_search_routes_to_duckduckgo() -> None:
    with patch.object(web_search.WebSearchAdapter, "search", return_value=[]) as mock_search:
        web_search._search("pytest error", WebSearchProvider.DUCKDUCKGO, max_results=3, timeout=10.0)
    mock_search.assert_called_once_with("pytest error", max_results=3)


def test_search_unimplemented_provider_raises() -> None:
    with pytest.raises(NotImplementedError, match="brave"):
        web_search._search("pytest error", WebSearchProvider.BRAVE, max_results=3, timeout=10.0)
