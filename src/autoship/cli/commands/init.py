"""The ``autoship init`` command."""

from __future__ import annotations

from pathlib import Path

import typer

from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.hardware_profiler import detect_hardware
from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.models.config import AppConfig
from autoship.plugin_manager import manager as plugin_manager
from autoship.utils.project_detector import detect_project_type
from autoship.utils.template import render_default_config

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.command(name="init")(init)


@app.command()
def init(
    ctx: typer.Context,
    project_type: str | None = typer.Option(None, "--type", help="Override project type"),
    output: Path = typer.Option(Path(".autoship.toml"), "--output", "-o", help="Config file path"),
) -> None:
    """Initialize an AutoShip configuration file for the current project."""
    config: AppConfig = ctx.obj["config"]
    i18n: I18n = get_i18n_from_ctx(ctx)
    audit: AuditLogger = ctx.obj["audit_logger"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes: bool = ctx.obj.get("yes", False)

    detected = project_type or detect_project_type(config.project_root)
    hardware = detect_hardware()
    context = CommandContext(
        command="init",
        project_root=config.project_root,
        config=config,
        dry_run=dry_run,
        yes=yes,
        trace_id=audit.trace_id,
    )

    audit.record(
        "init.start",
        {
            "detected": detected,
            "output": str(output),
            "recommended_tier": hardware.recommended_tier,
        },
    )
    plugin_manager.call("pre_init", context=context, fail_fast=False)

    if output.exists() and not yes and not typer.confirm(i18n._("init.overwrite", output=output)):
        typer.echo(i18n._("init.aborted"))
        audit.record("init.aborted", {"reason": "overwrite_declined"})
        raise typer.Exit(code=0)

    rendered = render_default_config(detected, default_tier=hardware.recommended_tier)

    if dry_run:
        typer.echo(i18n._("init.dry_run", output=output))
        typer.echo(rendered)
        audit.record("init.dry_run", {"output": str(output), "project_type": detected})
    else:
        output.write_text(rendered, encoding="utf-8")
        audit.record("init.done", {"output": str(output), "project_type": detected})
        typer.echo(i18n._("init.created", output=output))

    plugin_manager.call("post_init", context=context, fail_fast=False)
