"""Registry analytics, sync and dashboard commands."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import typer

from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.registry_client import RegistryClient
from autoship.core.registry_index import RegistryIndex
from autoship.models.config import AppConfig

app = typer.Typer()

BUNDLED_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "registry" / "plugins.json"


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="registry")


def _count_changes(current: dict[str, Any], fetched: dict[str, Any]) -> int:
    """Count added, removed and modified plugins between two index payloads."""
    current_plugins = {p.get("name"): p for p in current.get("plugins", [])}
    fetched_plugins = {p.get("name"): p for p in fetched.get("plugins", [])}

    current_names = set(current_plugins.keys())
    fetched_names = set(fetched_plugins.keys())

    added = fetched_names - current_names
    removed = current_names - fetched_names
    common = current_names & fetched_names
    modified = {name for name in common if current_plugins[name] != fetched_plugins[name]}

    return len(added) + len(removed) + len(modified)


@app.command("dashboard")
def dashboard(
    ctx: typer.Context,
    top: int = typer.Option(5, "--top", help="Number of plugins to show in top lists"),
) -> None:
    """Show registry analytics dashboard."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    index = RegistryIndex(ctx.obj.get("config"))
    plugins = index.list_plugins()

    if not plugins:
        typer.echo(i18n._("registry.empty"))
        return

    typer.echo(i18n._("registry.dashboard_title"))
    typer.echo(f"{'=' * 60}")
    typer.echo(f"Total plugins: {len(plugins)}")

    trust_counts = Counter(p.get("trust_level", "unknown") for p in plugins)
    typer.echo("\nBy trust level:")
    for level, count in trust_counts.most_common():
        typer.echo(f"  {level:<12} {count}")

    category_counts: Counter[str] = Counter()
    for plugin in plugins:
        for category in plugin.get("categories", []):
            category_counts[category] += 1
    if category_counts:
        typer.echo("\nBy category:")
        for category, count in category_counts.most_common():
            typer.echo(f"  {category:<12} {count}")

    def _rating_key(plugin: dict[str, Any]) -> float:
        rating = plugin.get("rating")
        return rating.get("score", 0.0) if rating else 0.0

    top_downloaded = sorted(plugins, key=lambda p: p.get("downloads", 0), reverse=True)[:top]
    typer.echo(f"\nTop {len(top_downloaded)} by downloads:")
    for plugin in top_downloaded:
        typer.echo(f"  {plugin['name']:<30} {plugin.get('downloads', 0)}")

    top_rated = sorted(
        [p for p in plugins if p.get("rating", {}).get("count", 0) > 0],
        key=_rating_key,
        reverse=True,
    )[:top]
    if top_rated:
        typer.echo(f"\nTop {len(top_rated)} by rating:")
        for plugin in top_rated:
            rating = plugin["rating"]
            typer.echo(f"  {plugin['name']:<30} {rating['score']:.1f} ({rating['count']})")


@app.command("sync")
def sync(
    ctx: typer.Context,
    output: Path = typer.Option(
        Path.home() / ".autoship" / "registry" / "plugins.json",
        "--output",
        "-o",
        help="Output path for the synced registry index",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force overwrite local cache"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without writing"),
) -> None:
    """Sync the plugin registry index from the remote source."""
    config: AppConfig = ctx.obj["config"]
    i18n: I18n = get_i18n_from_ctx(ctx)
    dry_run = ctx.obj.get("dry_run", False) or dry_run

    client = RegistryClient(config=config.registry)
    data = client.fetch_index(force=force)
    if data is None:
        typer.echo(i18n._("registry.sync_failed"), err=True)
        raise typer.Exit(code=1)

    current_index: dict[str, Any] = {"version": 1, "plugins": []}
    if BUNDLED_REGISTRY_PATH.exists():
        try:
            raw = BUNDLED_REGISTRY_PATH.read_text(encoding="utf-8")
            current_index = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            current_index = {"version": 1, "plugins": []}

    changes = _count_changes(current_index, data)

    if dry_run:
        typer.echo(i18n._("registry.sync_dry_run", count=changes))
        return

    payload = json.dumps(data, indent=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload, encoding="utf-8")

    BUNDLED_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    BUNDLED_REGISTRY_PATH.write_text(payload, encoding="utf-8")

    typer.echo(i18n._("registry.sync_done", count=changes, output=output))
