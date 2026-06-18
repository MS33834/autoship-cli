"""Configuration loading, merging, and validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from autoship.exceptions import ConfigError
from autoship.models.config import AppConfig

try:
    import tomllib  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]


DEFAULT_CONFIG_NAME = ".autoship.toml"
GLOBAL_CONFIG_DIR = Path.home() / ".config" / "autoship"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.toml"
ENV_PREFIX = "AUTOSHIP_"
SUPPORTED_CLEAN_TOOLS = {"autoflake", "black", "isort", "ruff"}


def _default_config() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "project_root": ".",
        "log_level": "INFO",
        "telemetry_enabled": False,
        "clean": {
            "enabled": True,
            "tools": ["autoflake", "black"],
            "dry_run": False,
            "exclude": [],
        },
        "commit": {
            "enabled": True,
            "max_tokens": 512,
            "conventional_commits": True,
            "auto_push": False,
        },
        "model": {
            "default_tier": 2,
            "fallback": True,
            "backends": [],
        },
    }


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            loader: Any = tomllib
            return cast(dict[str, Any], loader.load(f))
    except (OSError, tomllib.TOMLDecodeError) as exc:  # type: ignore[attr-defined]
        raise ConfigError(f"Failed to load config from {path}: {exc}") from exc


def _find_project_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    for candidate in [start, *start.parents]:
        if (candidate / DEFAULT_CONFIG_NAME).exists():
            return candidate
    return start


def _env_to_dict(prefix: str = ENV_PREFIX) -> dict[str, Any]:
    """Convert AUTOSHIP_* environment variables into a nested dict.

    Examples:
        AUTOSHIP_LOG_LEVEL=DEBUG -> {"log_level": "DEBUG"}
        AUTOSHIP_MODEL__DEFAULT_TIER=1 -> {"model": {"default_tier": 1}}
    """
    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix) :].lower().split("__")
        target = result
        for part in path[:-1]:
            target = target.setdefault(part, {})
        target[path[-1]] = _coerce_env_value(value)
    return result


def _coerce_env_value(value: str) -> Any:
    """Best-effort coercion of environment variable strings."""
    lower = value.lower()
    if lower in {"true", "1", "yes"}:
        return True
    if lower in {"false", "0", "no"}:
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge ``override`` into ``base`` recursively.

    Lists are replaced, not extended, to avoid surprising side effects.
    """
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def _validate_clean_tools(cfg: dict[str, Any]) -> None:
    """Validate that configured cleanup tools are supported."""
    tools = cfg.get("clean", {}).get("tools", [])
    unknown = [tool for tool in tools if tool not in SUPPORTED_CLEAN_TOOLS]
    if unknown:
        raise ConfigError(f"Unsupported clean tools: {', '.join(unknown)}")


def load_config(
    config_path: Path | None = None,
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> AppConfig:
    """Load and validate the full application configuration.

    Priority (high -> low):
        1. CLI overrides
        2. Environment variables (AUTOSHIP_*)
        3. Project-level ``.autoship.toml``
        4. Global ``~/.config/autoship/config.toml``
        5. Built-in defaults
    """
    base = _default_config()

    # Global config
    global_cfg = _load_toml(GLOBAL_CONFIG_FILE)
    merged = _deep_merge(base, global_cfg)

    # Project config
    if config_path is not None:
        project_cfg = _load_toml(config_path)
        project_root = config_path.parent
    else:
        project_root = project_root or _find_project_root()
        project_cfg = _load_toml(project_root / DEFAULT_CONFIG_NAME)

    merged = _deep_merge(merged, project_cfg)

    # Environment variables
    env_cfg = _env_to_dict()
    merged = _deep_merge(merged, env_cfg)

    # CLI overrides
    if cli_overrides:
        merged = _deep_merge(merged, cli_overrides)

    merged["project_root"] = str(project_root)

    _validate_clean_tools(merged)

    try:
        return AppConfig.model_validate(merged)
    except ValidationError as exc:
        raise ConfigError(f"Invalid configuration: {exc}") from exc
