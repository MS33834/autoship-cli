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
from autoship.core.i18n import get_i18n
from autoship.core.telemetry import TelemetryCollector
from autoship.exceptions import AutoShipError, ExitCode

app = typer.Typer(
    name="autoship",
    help="AutoShip: AI-assisted code shipping toolkit",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
)


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show actions without executing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive confirmations"),
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    lang: str | None = typer.Option(
        None, "--lang", help="Output language (en, zh, auto)", show_default=False
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


def _guess_command() -> str:
    """Infer the invoked subcommand from ``sys.argv``."""
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        return sys.argv[1]
    return "help"


def cli_entrypoint() -> int:
    """Top-level entry point used by ``autoship`` console script."""
    logger = structlog.get_logger()
    config = load_config()
    i18n = get_i18n(config.locale)
    telemetry = TelemetryCollector(enabled=config.telemetry_enabled)
    start = time.perf_counter()
    command = _guess_command()
    exit_code = 0
    exc_record: BaseException | None = None

    try:
        app()
    except typer.Exit as exc:
        exit_code = exc.exit_code
    except AutoShipError as exc:
        exit_code = exc.code
        exc_record = exc
        typer.secho(i18n._("error.prefix", exc=exc), fg=typer.colors.RED, err=True)
    except Exception as exc:
        exit_code = ExitCode.USAGE_ERROR
        exc_record = exc
        logger.exception("Unhandled exception")
        typer.secho(i18n._("unexpected_error.prefix", exc=exc), fg=typer.colors.RED, err=True)
    finally:
        telemetry.record(command, start, exit_code, exc=exc_record)

    return exit_code
