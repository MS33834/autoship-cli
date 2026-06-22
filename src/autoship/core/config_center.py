"""Configuration loading, merging, and validation."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from autoship.exceptions import ConfigError
from autoship.models.config import AppConfig

logger = logging.getLogger("autoship")

try:
    import tomllib  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
except ImportError:  # pragma: no cover
    import tomli as tomllib  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]


DEFAULT_CONFIG_NAME = ".autoship.toml"
TEAM_CONFIG_NAME = ".autoship.team.toml"
SYSTEM_CONFIG_FILE = Path("/etc/autoship.toml")
GLOBAL_CONFIG_DIR = Path.home() / ".config" / "autoship"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.toml"
ENV_PREFIX = "AUTOSHIP_"
SUPPORTED_CLEAN_TOOLS = {"autoflake", "black", "isort", "ruff"}

# Environment variables may only override fields explicitly listed here.
# Sensitive keys are blocked regardless of whether they appear in this list.
SENSITIVE_ENV_KEYS = frozenset({"siem_url", "siem_token", "base_url", "api_key"})
ENV_ALLOWLIST = frozenset({
    "log_level",
    "telemetry_enabled",
    "locale",
    "clean.enabled",
    "clean.tools",
    "clean.dry_run",
    "clean.exclude",
    "commit.enabled",
    "commit.max_tokens",
    "commit.conventional_commits",
    "commit.auto_push",
    "commit.allowed_editors",
    "security.enabled",
    "security.tools",
    "security.threshold",
    "security.fail_fast",
    "audit.log_dir",
    "audit.retention_days",
    "audit.redact_unknown_fields",
    "audit.siem_enabled",
    "audit.siem_max_failures",
    "sandbox.required",
    "web_search.enabled",
    "web_search.provider",
    "web_search.max_results",
    "web_search.timeout",
    "web_search.instance_url",
    "docker_ship.enabled",
    "docker_ship.default_image",
    "docker_ship.default_tag",
    "docker_ship.push",
    "docker_ship.build_args",
    "model.default_tier",
    "model.fallback",
    "verify.allowed_commands",
    "cache.enabled",
    "cache.ttl",
    "cache.dir",
    "registry.url",
    "registry.cache_enabled",
    "registry.cache_ttl_seconds",
    "registry.public_key",
    "llm.provider",
    "llm.model",
    "llm.timeout",
    "llm.max_tokens",
    "llm.api_version",
    "tools.git.path",
    "tools.git.sha256",
    "tools.docker.path",
    "tools.docker.sha256",
    "tools.twine.path",
    "tools.twine.sha256",
    "tools.gh.path",
    "tools.gh.sha256",
    "tools.patch.path",
    "tools.patch.sha256",
})


def _default_config() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "project_root": ".",
        "log_level": "INFO",
        "telemetry": {
            "enabled": False,
            "batch_size": 10,
            "timeout": 5.0,
            "allow_untrusted_endpoint": False,
        },
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
    except (OSError, tomllib.TOMLDecodeError) as exc:  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
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


def _env_var_name(path: list[str]) -> str:
    """Reconstruct the original environment variable name for a path."""
    return f"{ENV_PREFIX}{'__'.join(path).upper()}"


def _filter_env_cfg(cfg: dict[str, Any], path: list[str] | None = None) -> dict[str, Any]:
    """Drop environment overrides that are not in the allowlist or are sensitive.

    Only leaf values are checked. Nested dictionaries are recursed into and kept
    only if they contain at least one allowed leaf.
    """
    path = path or []
    filtered: dict[str, Any] = {}
    for key, value in cfg.items():
        current = [*path, key]
        if isinstance(value, dict):
            nested = _filter_env_cfg(cast(dict[str, Any], value), current)
            if nested:
                filtered[key] = nested
            continue
        dotted = ".".join(current)
        if key in SENSITIVE_ENV_KEYS or dotted not in ENV_ALLOWLIST:
            reason = "sensitive" if key in SENSITIVE_ENV_KEYS else "not in allowlist"
            logger.warning(
                "Ignoring disallowed environment override %s (%s)",
                _env_var_name(current),
                reason,
            )
            continue
        filtered[key] = value
    return filtered


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
            merged[key] = _deep_merge(merged[key], value)  # pyright: ignore[reportUnknownArgumentType]
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
        4. Team-level ``.autoship.team.toml``
        5. Global ``~/.config/autoship/config.toml``
        6. System ``/etc/autoship.toml``
        7. Built-in defaults
    """
    base = _default_config()

    # System config
    system_cfg = _load_toml(SYSTEM_CONFIG_FILE)
    merged = _deep_merge(base, system_cfg)

    # Global config
    global_cfg = _load_toml(GLOBAL_CONFIG_FILE)
    merged = _deep_merge(merged, global_cfg)

    # Resolve project root early so team config is looked up there
    if config_path is not None:
        project_root = config_path.parent
    else:
        project_root = project_root or _find_project_root()

    # Team config
    team_cfg = _load_toml(project_root / TEAM_CONFIG_NAME)
    merged = _deep_merge(merged, team_cfg)

    # Project config
    if config_path is not None:
        project_cfg = _load_toml(config_path)
    else:
        project_cfg = _load_toml(project_root / DEFAULT_CONFIG_NAME)

    merged = _deep_merge(merged, project_cfg)

    # Environment variables (filtered by allowlist)
    env_cfg = _filter_env_cfg(_env_to_dict())
    merged = _deep_merge(merged, env_cfg)

    # CLI overrides
    if cli_overrides:
        merged = _deep_merge(merged, cli_overrides)

    merged["project_root"] = str(project_root)

    _validate_clean_tools(merged)

    try:
        config: AppConfig = AppConfig.model_validate(merged)
        return config
    except ValidationError as exc:
        raise ConfigError(f"Invalid configuration: {exc}") from exc
