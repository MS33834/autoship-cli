"""Registry analytics and dashboard commands."""

from __future__ import annotations

from collections import Counter
from typing import Any

import typer

from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.registry_index import RegistryIndex

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="registry")


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
