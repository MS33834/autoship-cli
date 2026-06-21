"""Internal helpers shared by model backend providers."""

from __future__ import annotations

import httpx


def format_provider_error(provider_name: str, exc: Exception) -> str:
    """Return a redacted, provider-agnostic error message for ``exc``.

    ``httpx.RequestError`` string representations may contain the request URL
    or API key query parameters, so this helper avoids interpolating the raw
    exception text into user-facing messages.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        return f"{provider_name} returned HTTP {exc.response.status_code}"
    if isinstance(exc, httpx.TimeoutException):
        return f"{provider_name} request timed out"
    if isinstance(exc, httpx.RequestError):
        return f"{provider_name} request failed"
    if isinstance(exc, ValueError):
        return f"{provider_name} returned invalid JSON"
    return f"{provider_name} request failed"
