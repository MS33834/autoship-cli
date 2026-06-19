"""The ``autoship metrics`` command for observability."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.metrics import get_registry

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="metrics", help="Inspect runtime metrics")


@app.command("show")
def show(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output metrics as JSON"),
    reset: bool = typer.Option(False, "--reset", help="Reset metrics after displaying"),
) -> None:
    """Display collected runtime metrics."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = get_registry()
    snapshot = registry.snapshot()

    if json_output:
        typer.echo(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        _render_table(i18n, snapshot)

    if reset:
        registry.reset()


@app.command("export")
def export(
    ctx: typer.Context,
    output: Path = typer.Option(
        Path.home() / ".autoship" / "metrics.json",
        "--output",
        "-o",
        help="Path to write the metrics JSON file",
    ),
    reset: bool = typer.Option(False, "--reset", help="Reset metrics after exporting"),
) -> None:
    """Export collected metrics to a JSON file."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = get_registry()
    snapshot = registry.snapshot()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(i18n._("metrics.exported", path=str(output)))
    if reset:
        registry.reset()


def _render_table(i18n: I18n, snapshot: dict[str, dict[str, object]]) -> None:
    if not snapshot:
        typer.echo(i18n._("metrics.empty"))
        return

    typer.echo(i18n._("metrics.title"))
    typer.echo("-" * 70)
    for name, data in sorted(snapshot.items()):
        metric_type = data.get("type", "unknown")
        description = data.get("description", "")
        if metric_type == "counter":
            value = f"count={data['value']}"
        elif metric_type == "gauge":
            value = f"value={data['value']}"
        elif metric_type == "histogram":
            value = (
                f"count={data['count']} mean={data['mean']}ms "
                f"p50={data['p50']}ms p95={data['p95']}ms p99={data['p99']}ms"
            )
        else:
            value = str(data)
        typer.echo(f"{name:<40} {value}")
        if description:
            typer.echo(f"  {description}")
    typer.echo("-" * 70)
