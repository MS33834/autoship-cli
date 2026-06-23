"""Typer CLI entry point and global options."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import structlog
import typer

from autoship.cli import commands
from autoship.core.audit_logger import AuditLogger
from autoship.core.config_center import load_config
from autoship.core.i18n import I18n, get_i18n
from autoship.core.telemetry import TelemetryCollector
from autoship.exceptions import AutoShipError, ConfigError, ExitCode

_i18n = get_i18n()

app = typer.Typer(
    name="autoship",
    help=_i18n._("cli.help"),
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
)


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help=_i18n._("option.verbose")),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help=_i18n._("option.dry_run")),
    yes: bool = typer.Option(False, "--yes", "-y", help=_i18n._("option.yes")),
    config_path: Path | None = typer.Option(
        None, "--config", "-c", help=_i18n._("option.config_path")
    ),
    lang: str | None = typer.Option(
        None, "--lang", help=_i18n._("option.lang"), show_default=False
    ),
) -> None:
    """AutoShip global options."""
    ctx.ensure_object(dict)

    config = load_config(config_path=config_path)
    selected_lang = lang if isinstance(lang, str) and lang.lower() != "auto" else config.locale
    i18n = get_i18n(selected_lang)
    audit_logger = AuditLogger(config)
    audit_logger.record("cli.invoked", {"config_path": str(config_path) if config_path else None})

    ctx.obj["config"] = config
    ctx.obj["config_path"] = config_path
    ctx.obj["i18n"] = i18n
    ctx.obj["audit_logger"] = audit_logger
    ctx.obj["verbose"] = verbose
    ctx.obj["dry_run"] = dry_run
    ctx.obj["yes"] = yes


commands.register_all(app)


def _command_name(cmd) -> str | None:
    """Return the string name of a registered command or ``None``."""
    name = getattr(cmd, "name", None)
    return name if isinstance(name, str) and name else None


def _group_name(group) -> str | None:
    """Return the string name of a registered command group or ``None``.

    Typer stores the group name either directly on the parent ``TyperInfo`` or,
    when ``add_typer`` is called without an explicit ``name``, on the child
    ``Typer.info`` object. ``DefaultPlaceholder`` values are resolved best-effort.
    """
    name = getattr(group, "name", None)
    if isinstance(name, str) and name:
        return name
    child = getattr(group, "typer_instance", None)
    if child is not None:
        child_name = getattr(getattr(child, "info", None), "name", None)
        if isinstance(child_name, str) and child_name:
            return child_name
    return None


# Snapshot top-level command names immediately after registration. This avoids
# depending on the mutable ``app`` object at runtime, which matters for tests
# that patch ``main.app`` and for consistent error handling.
_KNOWN_COMMANDS: set[str] = set()
for _cmd in app.registered_commands:
    _name = _command_name(_cmd)
    if _name:
        _KNOWN_COMMANDS.add(_name)
for _group in app.registered_groups:
    _name = _group_name(_group)
    if _name:
        _KNOWN_COMMANDS.add(_name)


def _known_commands() -> set[str]:
    """Return the set of top-level subcommand names registered on ``app``."""
    return _KNOWN_COMMANDS


def _guess_command() -> str:
    """Infer the invoked subcommand from ``sys.argv``."""
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        return sys.argv[1]
    return "help"


def _is_unknown_command(command: str) -> bool:
    """Return True if ``command`` looks like a user-supplied but unknown subcommand."""
    return bool(command) and command not in _KNOWN_COMMANDS and command != "help"


def _print_suggestion(i18n: I18n, exc: AutoShipError) -> None:
    """Print a contextual next-step suggestion for common error types."""
    message = str(exc).lower()
    details = getattr(exc, "details", {}) or {}
    suggestion_key: str | None = None

    if isinstance(exc, ConfigError):
        suggestion_key = "error.suggestion.init"
    elif "api key" in message or (
        "model" in message and ("unreachable" in message or "backend" in message)
    ):
        suggestion_key = "error.suggestion.model_config"
    elif "command not found" in message or "not found on path" in message:
        suggestion_key = "error.suggestion.install_tool"
    elif "upload" in message:
        target = details.get("target") or "<target>"
        suggestion_key = "error.suggestion.upload_dry_run"
        typer.secho(f"\n💡 {i18n._(suggestion_key, target=target)}", fg=typer.colors.CYAN, err=True)
        return

    if suggestion_key:
        typer.secho(f"\n💡 {i18n._(suggestion_key)}", fg=typer.colors.CYAN, err=True)


def cli_entrypoint() -> int:
    """Top-level entry point used by ``autoship`` console script."""
    logger = structlog.get_logger()
    config = load_config()
    i18n = get_i18n(config.locale)
    telemetry = TelemetryCollector(
        enabled=config.telemetry.enabled,
        endpoint=str(config.telemetry.endpoint) if config.telemetry.endpoint else None,
        timeout=config.telemetry.timeout,
        allow_untrusted=config.telemetry.allow_untrusted_endpoint,
        batch_size=config.telemetry.batch_size,
    )
    start = time.perf_counter()
    command = _guess_command()
    exit_code = 0
    exc_record: BaseException | None = None

    if _is_unknown_command(command):
        typer.secho(i18n._("cli.unknown_command", command=command), fg=typer.colors.RED, err=True)
        typer.secho(
            f"💡 {i18n._('cli.unknown_command.suggestion')}",
            fg=typer.colors.CYAN,
            err=True,
        )
        telemetry.record(command, start, ExitCode.USAGE_ERROR, exc=None)
        telemetry.flush()
        return ExitCode.USAGE_ERROR

    try:
        app()
    except typer.Exit as exc:
        exit_code = exc.exit_code
    except AutoShipError as exc:
        exit_code = exc.code
        exc_record = exc
        typer.secho(i18n._("error.prefix", exc=exc), fg=typer.colors.RED, err=True)
        _print_suggestion(i18n, exc)
    except Exception as exc:
        exit_code = ExitCode.USAGE_ERROR
        exc_record = exc
        logger.exception("Unhandled exception")
        typer.secho(i18n._("unexpected_error.prefix", exc=exc), fg=typer.colors.RED, err=True)
        typer.secho(
            f"\n💡 {i18n._('error.suggestion.doctor')}",
            fg=typer.colors.CYAN,
            err=True,
        )
    finally:
        telemetry.record(command, start, exit_code, exc=exc_record)
        telemetry.flush()

    return exit_code
