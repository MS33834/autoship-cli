"""The ``autoship upload`` command."""

from __future__ import annotations

import subprocess
from typing import Any, cast

import typer

from autoship.adapters.upload import get_uploader
from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.i18n import I18n, get_i18n, get_i18n_from_ctx
from autoship.exceptions import UploadError
from autoship.plugin_manager import manager as plugin_manager

_i18n = get_i18n()
app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.command(name="upload", help=_i18n._("upload.help"))(upload)


@app.command(name="upload")
def upload(
    ctx: typer.Context,
    target: str = typer.Option(..., "--target", help=_i18n._("upload.option.target")),
    image: str | None = typer.Option(None, "--image", help=_i18n._("upload.option.image")),
    tag: str | None = typer.Option(None, "--tag", "-t", help=_i18n._("upload.option.tag")),
    artifacts: list[str] | None = typer.Option(
        None, "--artifact", help=_i18n._("upload.option.artifact")
    ),
    repository: str | None = typer.Option(
        None, "--repository", help=_i18n._("upload.option.repository")
    ),
    repository_url: str | None = typer.Option(
        None, "--repository-url", help=_i18n._("upload.option.repository_url")
    ),
    registry: str | None = typer.Option(None, "--registry", help=_i18n._("upload.option.registry")),
) -> None:
    """Upload artifacts to a configured target."""
    from autoship.adapters.upload.pypi import PyPIUploader

    config = ctx.obj["config"]
    i18n: I18n = get_i18n_from_ctx(ctx)
    audit: AuditLogger = ctx.obj["audit_logger"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes: bool = ctx.obj.get("yes", False)
    verbose: bool = ctx.obj.get("verbose", False)

    # Direct unit-test invocations may receive typer.Option objects as defaults.
    image = image if isinstance(image, str) else None
    tag = tag if isinstance(tag, str) else None
    artifacts = artifacts if isinstance(artifacts, list) else None
    repository = repository if isinstance(repository, str) else None
    repository_url = repository_url if isinstance(repository_url, str) else None
    registry = registry if isinstance(registry, str) else None

    uploader_cfg: dict[str, Any] = {"target": target}
    if image:
        uploader_cfg["image"] = image
    if tag:
        uploader_cfg["tag"] = tag
    if artifacts:
        uploader_cfg["artifacts"] = artifacts
    if repository:
        uploader_cfg["repository"] = repository
    if repository_url:
        if not PyPIUploader.is_safe_repository_url(repository_url):
            raise UploadError(i18n._("upload.repository_url_invalid"))
        uploader_cfg["repository_url"] = repository_url
    if registry:
        uploader_cfg["registry"] = registry

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

    if dry_run:
        audit.record(
            "upload.dry_run",
            {"target": target, "details": result.details},
        )
        plugin_manager.call("post_upload", context=context, fail_fast=False)
        typer.echo(
            i18n._(
                "upload.dry_run",
                target=target,
                details=_format_dry_run_details(result.details),
            )
        )
        return

    audit.record("upload.done", {"target": target, "result": result.details})
    plugin_manager.call("post_upload", context=context, fail_fast=False)
    if result.url:
        typer.echo(i18n._("upload.result_url", target=target, url=result.url))
    else:
        typer.echo(i18n._("upload.result", target=target))


def _format_dry_run_details(details: dict[str, Any] | None) -> str:
    """Format dry-run details for terminal output."""
    if not details:
        return ""
    lines: list[str] = []
    for key, value in details.items():
        if key == "dry_run":
            continue
        if isinstance(value, list):
            seq = cast(list[object], value)
            parts: list[str] = [str(v) for v in seq]
            display_value = ", ".join(parts)
        else:
            display_value = str(value)
        lines.append(f"  {key}: {display_value}")
    return "\n".join(lines)
