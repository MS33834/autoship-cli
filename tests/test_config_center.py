"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from autoship.core.config_center import (
    _coerce_env_value,
    _deep_merge,
    _env_to_dict,
    _find_project_root,
    load_config,
)
from autoship.exceptions import ConfigError
from autoship.models.config import AppConfig


def test_default_config(project_root: Path) -> None:
    cfg = load_config(project_root=project_root)
    assert isinstance(cfg, AppConfig)
    assert cfg.schema_version == 1
    assert cfg.log_level == "INFO"
    assert cfg.clean.tools == ["autoflake", "black"]


def test_load_from_file(project_root: Path) -> None:
    config_file = project_root / ".autoship.toml"
    config_file.write_text(
        'schema_version = 1\nlog_level = "DEBUG"\n[clean]\ntools = ["ruff"]\n',
        encoding="utf-8",
    )
    cfg = load_config(config_path=config_file)
    assert cfg.log_level == "DEBUG"
    assert cfg.clean.tools == ["ruff"]


def test_invalid_config_raises(project_root: Path) -> None:
    config_file = project_root / ".autoship.toml"
    config_file.write_text('schema_version = "not-an-int"\n', encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config_path=config_file)


def test_unsupported_clean_tool_raises(project_root: Path) -> None:
    config_file = project_root / ".autoship.toml"
    config_file.write_text('[clean]\ntools = ["unknown-tool"]\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="Unsupported clean tools"):
        load_config(config_path=config_file)


def test_supported_clean_tool_accepts(project_root: Path) -> None:
    config_file = project_root / ".autoship.toml"
    config_file.write_text('[clean]\ntools = ["ruff"]\n', encoding="utf-8")
    cfg = load_config(config_path=config_file)
    assert cfg.clean.tools == ["ruff"]


def test_find_project_root(project_root: Path) -> None:
    config_file = project_root / ".autoship.toml"
    config_file.write_text("schema_version = 1\n", encoding="utf-8")
    nested = project_root / "src" / "nested"
    nested.mkdir(parents=True)
    assert _find_project_root(nested) == project_root


def test_env_to_dict(monkeypatch) -> None:
    monkeypatch.setenv("AUTOSHIP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("AUTOSHIP_MODEL__DEFAULT_TIER", "1")
    env_cfg = _env_to_dict()
    assert env_cfg["log_level"] == "DEBUG"
    assert env_cfg["model"]["default_tier"] == 1


def test_coerce_env_value() -> None:
    assert _coerce_env_value("true") is True
    assert _coerce_env_value("false") is False
    assert _coerce_env_value("42") == 42
    assert _coerce_env_value("3.14") == 3.14
    assert _coerce_env_value("hello") == "hello"


def test_deep_merge() -> None:
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}}
    merged = _deep_merge(base, override)
    assert merged["a"] == 1
    assert merged["b"] == {"c": 99, "d": 3}
