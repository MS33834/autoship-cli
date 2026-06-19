"""The ``autoship upload`` command."""

from __future__ import annotations

import subprocess
from typing import Any

import typer

from autoship.adapters.upload import get_uploader
from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.exceptions import UploadError
from autoship.plugin_manager import manager as plugin_manager

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.command(name="upload")(upload)


@app.command(name="upload")
def upload(
    ctx: typer.Context,
    target: str = typer.Option(..., "--target", help="Upload target, e.g. pypi/docker/github"),
    image: str | None = typer.Option(None, "--image", help="Docker image name"),
    tag: str | None = typer.Option(
        None, "--tag", "-t", help="Docker image tag or GitHub release tag"
    ),
    artifacts: list[str] | None = typer.Option(None, "--artifact", help="Artifacts to upload"),
) -> None:
    """Upload artifacts to a configured target."""
    config = ctx.obj["config"]
    i18n: I18n = get_i18n_from_ctx(ctx)
    audit: AuditLogger = ctx.obj["audit_logger"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes: bool = ctx.obj.get("yes", False)
    verbose: bool = ctx.obj.get("verbose", False)

    uploader_cfg: dict[str, Any] = {"target": target}
    if image:
        uploader_cfg["image"] = image
    if tag:
        uploader_cfg["tag"] = tag
    if artifacts:
        uploader_cfg["artifacts"] = artifacts

    context = CommandContext(
        command="upload",
        project_root=config.project_root,
        config=config,
        dry_run=dry_run,
        yes=yes,
        trace_id=audit.trace_id,
        extras=uploader_cfg,
    )

    audit.record("upload.start", {"target": target, "config": uploader_cfg})
    plugin_manager.call("pre_upload", context=context, fail_fast=False)

    uploader = get_uploader(target, config.project_root, uploader_cfg)

    if not dry_run and not yes and not typer.confirm(i18n._("upload.confirm", target=target)):
        typer.echo(i18n._("upload.aborted"))
        audit.record("upload.aborted", {"reason": "user_declined"})
        raise typer.Exit(code=0)

    try:
        result = uploader.upload(dry_run=dry_run, verbose=verbose)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        error = UploadError(i18n._("upload.failed", target=target, exc=exc))
        audit.record(
            "upload.error",
            {"target": target, "error": str(exc)},
        )
        plugin_manager.call("on_error", context=context, error=error, fail_fast=False)
        raise error from exc

    audit.record("upload.done", {"target": target, "result": result.details})
    plugin_manager.call("post_upload", context=context, fail_fast=False)
    if result.url:
        typer.echo(i18n._("upload.result_url", target=target, url=result.url))
    else:
        typer.echo(i18n._("upload.result", target=target))
