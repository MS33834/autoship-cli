"""Unified sensitive-data redaction for AutoShip.

This module provides the single source of truth for:
- Sensitive key names that must always be masked.
- Secret-like value patterns (API tokens, private keys, JWTs, etc.).
- Helpers to redact free-form text, dictionary values, and nested structures.

All callers (audit logger, telemetry, config display) import from here so that
redaction behaviour never diverges between subsystems.
"""

from __future__ import annotations

import re
from typing import Any, cast

# ── Sensitive key names ──────────────────────────────────────────────
# Union of all previously separate key sets (audit_logger, telemetry, config).
SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "token",
        "api_key",
        "apikey",
        "api-key",
        "password",
        "passwd",
        "pwd",
        "secret",
        "siem_token",
        "key",
        "private",
        "private_key",
        "privatekey",
        "credentials",
        "auth",
        "authorization",
        "access_token",
        "refresh_token",
        "cookie",
        "session",
        "email",
        "phone",
        "cx",
        "public_key",
        "base_url",
    }
)

# ── Secret-like value patterns ───────────────────────────────────────
# Union of all previously separate pattern sets.
SENSITIVE_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # GitHub personal access token (classic)
    re.compile(r"ghp_[A-Za-z0-9_]{36}"),
    # GitHub fine-grained personal access token
    re.compile(r"github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59}"),
    # OpenAI API key
    re.compile(r"sk-[a-zA-Z0-9]{48}"),
    # AWS access key id
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # PEM/SSH private key block
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY-----"),
    # JWT (header.payload.signature)
    re.compile(r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"),
    # Long hex strings (32+ chars) — hashes/tokens
    re.compile(r"[a-f0-9]{32,}", re.IGNORECASE),
    # Generic JWT-like dotted tokens
    re.compile(r"[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}"),
    # Email addresses
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
)


def is_sensitive_key(key: str) -> bool:
    """Return True if *key* (case-insensitive) indicates a sensitive field.

    Uses exact match against the known set of sensitive key names, plus
    substring matching for compound keys (e.g. ``user_token``, ``api_key_id``)
    to avoid missing variants.
    """
    lower = key.lower()
    if lower in SENSITIVE_KEYS:
        return True
    # Check compound keys: split on common separators and check each part.
    parts = re.split(r"[_\-. ]", lower)
    return any(part in SENSITIVE_KEYS for part in parts if part)


def redact_text(text: str) -> str:
    """Redact a free-form string when it contains a secret-like pattern.

    Returns ``"***"`` if any known secret pattern matches, otherwise the
    original text unchanged.
    """
    if any(pattern.search(text) for pattern in SENSITIVE_VALUE_PATTERNS):
        return "***"
    return text


def redact_scalar(value: Any) -> Any:
    """Redact a scalar value if it contains a secret-like pattern."""
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_dict(
    data: dict[str, Any],
    *,
    mask: str = "***",
    redact_unknown: bool = False,
    safe_keys: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Recursively redact sensitive keys and secret-like values in *data*.

    Parameters
    ----------
    data:
        The dictionary to redact.
    mask:
        The string to replace sensitive values with.
    redact_unknown:
        When True, any key not in *safe_keys* is treated as sensitive.
    safe_keys:
        Keys considered safe when *redact_unknown* is True.
    """
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        key_lower = key.lower()
        if is_sensitive_key(key_lower):
            redacted[key] = mask
        elif redact_unknown and safe_keys is not None and key_lower not in safe_keys:
            redacted[key] = _redact_unknown_value(value, mask=mask)
        elif isinstance(value, dict):
            redacted[key] = redact_dict(
                cast(dict[str, Any], value),
                mask=mask,
                redact_unknown=redact_unknown,
                safe_keys=safe_keys,
            )
        elif isinstance(value, list):
            redacted[key] = [
                redact_dict(
                    cast(dict[str, Any], item),
                    mask=mask,
                    redact_unknown=redact_unknown,
                    safe_keys=safe_keys,
                )
                if isinstance(item, dict)
                else redact_scalar(item)
                for item in cast(list[Any], value)
            ]
        else:
            redacted[key] = redact_scalar(value)
    return redacted


def _redact_unknown_value(value: Any, *, mask: str = "***") -> Any:
    """Redact an unknown value recursively."""
    if isinstance(value, dict):
        return {
            k: _redact_unknown_value(v, mask=mask) for k, v in cast(dict[str, Any], value).items()
        }
    if isinstance(value, list):
        return [_redact_unknown_value(item, mask=mask) for item in cast(list[Any], value)]
    return mask
