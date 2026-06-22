"""``autoship config`` command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import structlog
import tomli_w
import typer

from autoship.core.config_center import DEFAULT_CONFIG_NAME
from autoship.exceptions import ConfigError

logger = structlog.get_logger()

app = typer.Typer(name="config", help="Inspect and manage AutoShip configuration.")

# Keys whose values should be redacted when printing configuration.
SENSITIVE_KEYS = frozenset({"api_key", "siem_token", "base_url", "cx", "public_key"})

try:
    import tomllib  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
except ImportError:  # pragma: no cover
    import tomli as tomllib  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]


def _redact(value: Any) -> Any:
    """Recursively redact sensitive dictionary values."""
    if isinstance(value, dict):
        mapping = cast(dict[str, Any], value)
        return {k: "***" if k in SENSITIVE_KEYS else _redact(v) for k, v in mapping.items()}
    if isinstance(value, list):
        sequence = cast(list[Any], value)
        return [_redact(item) for item in sequence]
    return value


def _drop_none(value: Any) -> Any:
    """Recursively drop ``None`` values so output is TOML serializable."""
    if isinstance(value, dict):
        mapping = cast(dict[str, Any], value)
        return {k: _drop_none(v) for k, v in mapping.items() if v is not None}
    if isinstance(value, list):
        sequence = cast(list[Any], value)
        return [_drop_none(item) for item in sequence if item is not None]
    return value


def _dotted_get(cfg: dict[str, Any], key: str) -> Any:
    """Retrieve a nested configuration value by dotted key."""
    parts = key.split(".")
    target: Any = cfg
    for part in parts:
        if not isinstance(target, dict):
            raise ConfigError(f"Key '{key}' not found in configuration")
        mapping = cast(dict[str, Any], target)
        if part not in mapping:
            raise ConfigError(f"Key '{key}' not found in configuration")
        target = mapping[part]
    return target


def _target_path(ctx: typer.Context) -> Path:
    """Return the configuration file path to modify."""
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    if config_path is not None:
        return config_path
    project_root: Path = ctx.obj["config"].project_root
    return project_root / DEFAULT_CONFIG_NAME


def _load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file or return an empty dict if it does not exist."""
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]


@app.command("list")
def list_config(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show effective configuration (sensitive values are redacted)."""
    cfg = ctx.obj["config"].model_dump(mode="json")
    cfg = _redact(cfg)
    if json_output:
        typer.echo(json.dumps(cfg, indent=2))
    else:
        typer.echo(tomli_w.dumps(_drop_none(cfg)).strip())


@app.command("get")
def get_config(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Dotted configuration key, e.g. model.default_tier"),
) -> None:
    """Get a single configuration value."""
    cfg = ctx.obj["config"].model_dump(mode="json")
    try:
        value = _dotted_get(cfg, key)
    except ConfigError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    if isinstance(value, (dict, list)):
        typer.echo(json.dumps(value, indent=2))
    else:
        typer.echo(str(value))


@app.command("telemetry")
def telemetry_config(
    ctx: typer.Context,
    enable: bool = typer.Option(False, "--enable", help="Enable telemetry"),
    disable: bool = typer.Option(False, "--disable", help="Disable telemetry"),
    status: bool = typer.Option(False, "--status", help="Show current telemetry status"),
) -> None:
    """Enable, disable, or view telemetry setting."""
    cfg = ctx.obj["config"]
    if status or (not enable and not disable):
        state = "enabled" if cfg.telemetry_enabled else "disabled"
        typer.echo(f"Telemetry is {state}.")
        return

    target = _target_path(ctx)
    data = _load_toml(target)
    data["telemetry_enabled"] = enable if enable else not disable
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(tomli_w.dumps(data), encoding="utf-8")
    state = "enabled" if data["telemetry_enabled"] else "disabled"
    typer.echo(f"Telemetry {state}. Configuration written to {target}")


def register(parent: typer.Typer) -> None:
    """Register the config command group."""
    parent.add_typer(app)
