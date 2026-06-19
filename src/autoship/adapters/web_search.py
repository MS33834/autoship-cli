"""Lightweight web search adapter for AI-assisted debugging.

The default provider is DuckDuckGo Lite, which does not require an API key.
Because this sends error snippets to a public service, it is disabled by default
and must be explicitly enabled via configuration.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, TypedDict, cast
from urllib.parse import quote_plus

import httpx


@dataclass
class WebSearchResult:
    """A single web search result."""

    title: str
    url: str
    snippet: str


class WebSearchError(Exception):
    """Raised when a web search request fails."""


class _BraveWebResult(TypedDict, total=False):
    title: str
    url: str
    description: str


class _BraveWebSection(TypedDict, total=False):
    results: list[_BraveWebResult]


class _BraveSearchResponse(TypedDict, total=False):
    query: dict[str, Any]
    web: _BraveWebSection


class WebSearchAdapter:
    """Search the web and return a list of results."""

    _DUCKDUCKGO_LITE = "https://html.duckduckgo.com/html/"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        """Search for ``query`` and return up to ``max_results`` items."""
        url = f"{self._DUCKDUCKGO_LITE}?q={quote_plus(query)}"
        try:
            response = httpx.get(url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebSearchError(f"Web search request failed: {exc}") from exc

        return self._parse_duckduckgo(response.text, max_results)

    def _parse_duckduckgo(self, html_text: str, max_results: int) -> list[WebSearchResult]:
        """Parse DuckDuckGo Lite HTML results."""
        results: list[WebSearchResult] = []
        # Each result is wrapped in a .result container
        containers = re.split(r'<div class="result[^"]*"', html_text)

        for container in containers[1:]:
            if len(results) >= max_results:
                break

            title_match = re.search(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', container, re.S)
            if not title_match:
                continue

            title = html.unescape(self._strip_tags(title_match.group(1)))
            link_match = re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"', container)
            url = html.unescape(link_match.group(1)) if link_match else ""

            snippet_match = re.search(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', container, re.S
            )
            snippet = (
                html.unescape(self._strip_tags(snippet_match.group(1))) if snippet_match else ""
            )

            if title and url:
                results.append(WebSearchResult(title=title, url=url, snippet=snippet))

        return results

    @staticmethod
    def _strip_tags(text: str) -> str:
        """Remove HTML tags and collapse whitespace."""
        cleaned = re.sub(r"<[^>]+>", "", text)
        return re.sub(r"\s+", " ", cleaned).strip()


class BraveSearchAdapter:
    """Search the web using the Brave Search API."""

    _BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        """Search for ``query`` via Brave and return up to ``max_results`` items."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        params: dict[str, str | int] = {"q": query, "count": max_results}
        try:
            response = httpx.get(
                self._BRAVE_SEARCH_URL,
                headers=headers,
                params=params,
                timeout=self.timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebSearchError(f"Brave search request failed: {exc}") from exc

        payload = cast(_BraveSearchResponse, response.json())
        return self._parse_brave(payload, max_results)

    def _parse_brave(
        self, payload: _BraveSearchResponse, max_results: int
    ) -> list[WebSearchResult]:
        """Parse Brave Search JSON response."""
        results: list[WebSearchResult] = []
        web = payload.get("web")
        if web is None:
            return results

        items = web.get("results")
        if items is None:
            return results

        for item in items:
            if len(results) >= max_results:
                break
            title = item.get("title")
            url = item.get("url")
            snippet = item.get("description")
            if title and url:
                results.append(
                    WebSearchResult(
                        title=title,
                        url=url,
                        snippet=snippet or "",
                    )
                )

        return results


def format_results(results: list[WebSearchResult]) -> str:
    """Format search results for inclusion in a model prompt."""
    if not results:
        return "No web search results."
    lines: list[str] = []
    for index, result in enumerate(results, start=1):
        lines.append(f"{index}. {result.title}\n   {result.url}\n   {result.snippet}")
    return "\n\n".join(lines)
