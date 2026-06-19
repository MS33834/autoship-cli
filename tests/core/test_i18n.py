"""Tests for the i18n module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from autoship.core.i18n import I18n, _detect_locale, get_i18n


def test_i18n_returns_translation() -> None:
    i18n = get_i18n("en")
    assert i18n._("clean.noop") == "Already clean."


def test_i18n_formats_arguments() -> None:
    i18n = get_i18n("en")
    assert i18n._("clean.complete") == "Clean complete."
    assert i18n._("init.created", output=".autoship.toml") == "Created .autoship.toml"


def test_i18n_falls_back_to_key() -> None:
    i18n = get_i18n("en")
    assert i18n._("missing.key") == "missing.key"


def test_i18n_chinese_catalog() -> None:
    i18n = get_i18n("zh")
    assert i18n._("clean.noop") == "已经是干净的。"
    assert i18n._("doctor.title") == "AutoShip 环境诊断"


def test_i18n_unknown_language_falls_back_to_keys() -> None:
    i18n = get_i18n("xx")
    assert i18n.lang == "xx"
    assert i18n._("clean.noop") == "clean.noop"


def test_detect_locale_from_autoship_lang() -> None:
    with patch.dict(os.environ, {"AUTOSHIP_LANG": "zh_CN.UTF-8"}, clear=False):
        assert _detect_locale() == "zh"


def test_detect_locale_defaults_to_english() -> None:
    with (
        patch.dict(os.environ, {"AUTOSHIP_LANG": "", "LANG": ""}, clear=True),
        patch("locale.getlocale", side_effect=ValueError("no locale")),
    ):
        assert _detect_locale() == "en"


def test_get_i18n_uses_environment_when_no_arg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOSHIP_LANG", "zh")
    i18n = get_i18n()
    assert i18n.lang == "zh"
    assert i18n._("clean.noop") == "已经是干净的。"


def test_locale_files_are_shipped() -> None:
    locales_dir = Path(__file__).resolve().parents[2] / "src" / "autoship" / "locales"
    assert (locales_dir / "en.json").exists()
    assert (locales_dir / "zh.json").exists()


def test_i18n_class_basic_usage() -> None:
    translator = I18n("test", {"greeting": "Hello {name}"})
    assert translator._("greeting", name="World") == "Hello World"
