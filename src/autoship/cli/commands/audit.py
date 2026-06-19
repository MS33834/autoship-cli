"""The ``autoship audit`` command."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer

from autoship.core.audit_logger import AuditLogger
from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.models.config import AppConfig

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="audit")


def get_audit_logger_from_ctx(ctx: typer.Context) -> AuditLogger:
    """Return the ``AuditLogger`` stored in ``ctx.obj`` or build one from config."""
    obj = getattr(ctx, "obj", None)
    audit_logger = obj.get("audit_logger") if obj else None
    if isinstance(audit_logger, AuditLogger):
        return audit_logger
    config = obj.get("config") if obj else None
    if isinstance(config, AppConfig):
        return AuditLogger(config)
    return AuditLogger(AppConfig())


def _parse_since(value: str) -> datetime:
    """Parse ``--since`` value as ISO datetime or relative days (``1d``, ``7d``)."""
    stripped = value.strip().lower()
    if stripped.endswith("d"):
        try:
            days = int(stripped[:-1])
        except ValueError as exc:
            raise typer.BadParameter(f"Invalid relative time: {value}") from exc
        return datetime.now(timezone.utc) - timedelta(days=days)
    try:
        parsed = datetime.fromisoformat(stripped)
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@app.command("export")
def export_logs(
    ctx: typer.Context,
    since: str | None = typer.Option(
        None,
        "--since",
        "-s",
        help="Export records after this time (ISO or 1d/7d/30d)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
) -> None:
    """Export audit logs to a JSON Lines file."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    audit_logger = get_audit_logger_from_ctx(ctx)
    since_dt = _parse_since(since) if since else None
    exported_path = audit_logger.export(since=since_dt, output=output)
    count = 0
    try:
        text = exported_path.read_text()
        count = len([line for line in text.splitlines() if line.strip()])
    except OSError:
        pass
    typer.echo(i18n._("audit.export_done", path=exported_path, count=count))


@app.command("cleanup")
def cleanup_logs(
    ctx: typer.Context,
    retention_days: int | None = typer.Option(
        None,
        "--retention-days",
        help="Retention period in days",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions without executing"),
) -> None:
    """Remove audit log files older than the retention period."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    audit_logger = get_audit_logger_from_ctx(ctx)
    if dry_run:
        typer.echo(i18n._("audit.cleanup_dry_run"))
        return
    removed = audit_logger.cleanup(retention_days=retention_days)
    typer.echo(i18n._("audit.cleanup_done", removed=removed))
