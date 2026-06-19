"""Lightweight JSON-based internationalization support."""

from __future__ import annotations

import json
import locale as _locale
import logging
import os
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger("autoship")


class I18n:
    """Simple key-based translator backed by JSON dictionaries."""

    def __init__(self, lang: str, catalog: dict[str, str]) -> None:
        self.lang = lang
        self.catalog = catalog

    def _(self, key: str, **kwargs: Any) -> str:
        """Return the translated string for ``key`` with optional formatting.

        If formatting fails (e.g. missing or malformed placeholders), the raw
        template is returned and a warning is logged so that callers never
        crash because of a bad translation or missing substitution value.
        """
        template = self.catalog.get(key, key)
        if not kwargs:
            return template
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError, IndexError) as exc:
            logger.warning("Failed to format i18n key %r: %s", key, exc)
            return template


def _locales_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "locales"


def _load_catalog(lang: str) -> dict[str, str]:
    path = _locales_dir() / f"{lang}.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        items: dict[str, str] = {}
        for raw_key, raw_value in cast(dict[Any, Any], data).items():
            if isinstance(raw_value, str):
                items[str(raw_key)] = raw_value
        return items
    return {}


def _detect_locale() -> str:
    """Detect preferred language from environment or system locale."""
    env_lang = os.environ.get("AUTOSHIP_LANG") or os.environ.get("LANG", "")
    normalized = env_lang.split(".")[0].replace("-", "_").lower()
    if normalized.startswith("zh"):
        return "zh"
    if normalized.startswith("en"):
        return "en"

    try:
        system_locale, _ = _locale.getlocale()
    except (_locale.Error, AttributeError, ValueError) as exc:
        logger.debug("Could not detect system locale: %s", exc)
        return "en"
    if system_locale:
        normalized = system_locale.split(".")[0].replace("-", "_").lower()
        if normalized.startswith("zh"):
            return "zh"
    return "en"


def get_i18n(lang: str | None = None) -> I18n:
    """Create an ``I18n`` instance for ``lang`` or the detected default."""
    target = (lang if lang and lang.lower() != "auto" else _detect_locale()).lower()
    catalog = _load_catalog(target)
    return I18n(target, catalog)


def get_i18n_from_ctx(ctx: Any) -> I18n:
    """Return the ``I18n`` instance stored in ``ctx.obj`` or a default one."""
    obj: dict[str, Any] | None = getattr(ctx, "obj", None)
    i18n = obj.get("i18n") if obj else None
    if isinstance(i18n, I18n):
        return i18n
    return get_i18n()
