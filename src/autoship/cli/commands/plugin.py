"""The ``autoship plugin`` command."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import typer

from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.plugin_registry import PluginRegistry, PluginSpec, TrustLevel
from autoship.core.registry_index import RegistryIndex
from autoship.exceptions import PluginError

app = typer.Typer()


def _pip_cmd() -> list[str]:
    """Return the preferred package installer command (uv or pip)."""
    if shutil.which("uv"):
        return ["uv", "pip"]
    return ["pip"]


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="plugin")


@app.command("list")
def list_plugins(
    ctx: typer.Context,
) -> None:
    """List registered plugins and their trust levels."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = PluginRegistry()
    plugins = registry.list()
    if not plugins:
        typer.echo(i18n._("plugin.no_plugins"))
        return

    typer.echo(
        f"{i18n._('plugin.header.name'):<30} "
        f"{i18n._('plugin.header.version'):<10} "
        f"{i18n._('plugin.header.trust'):<12} "
        f"{i18n._('plugin.header.source')}"
    )
    for plugin in plugins:
        typer.echo(
            f"{plugin.name:<30} {plugin.version:<10} {plugin.trust_level.value:<12} {plugin.source}"
        )


@app.command("search")
def search_plugins(
    ctx: typer.Context,
    keyword: str | None = typer.Argument(None, help="Keyword to search in name or description"),
) -> None:
    """Search the official plugin registry index."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    index = RegistryIndex()
    plugins = index.search(keyword)
    if not plugins:
        typer.echo(i18n._("plugin.no_matches"))
        return

    typer.echo(
        f"{i18n._('plugin.header.name'):<30} "
        f"{i18n._('plugin.header.version'):<10} "
        f"{i18n._('plugin.header.trust'):<12} "
        f"{i18n._('plugin.header.description')}"
    )
    for plugin in plugins:
        typer.echo(
            f"{plugin['name']:<30} {plugin.get('version', '?'):<10} "
            f"{plugin.get('trust_level', 'community'):<12} {plugin.get('description', '')}"
        )


@app.command("install")
def install(
    ctx: typer.Context,
    source: str = typer.Argument(..., help="Package spec or plugin name from registry"),
    name: str | None = typer.Option(None, "--name", help="Plugin name to register"),
    version: str | None = typer.Option(None, "--version", help="Plugin version"),
    trust: TrustLevel | None = typer.Option(None, "--trust", help="Initial trust level"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions without executing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmations"),
) -> None:
    """Install a plugin package and register it locally."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = PluginRegistry()
    index = RegistryIndex()
    indexed = index.get(source)

    if indexed:
        plugin_name = name or indexed["name"]
        package = indexed["package"]
        plugin_version = version or indexed.get("version", "0.0.0")
        plugin_trust = trust or TrustLevel(indexed.get("trust_level", "verified"))
        source_for_pip = package
    else:
        plugin_name = name or Path(source).name
        package = source
        plugin_version = version or "0.0.0"
        plugin_trust = trust or TrustLevel.COMMUNITY
        source_for_pip = source

    if (
        not dry_run
        and not yes
        and not typer.confirm(
            i18n._("plugin.install_confirm", plugin_name=plugin_name, source_for_pip=source_for_pip)
        )
    ):
        typer.echo(i18n._("common.aborted"))
        raise typer.Exit(code=0)

    if dry_run:
        typer.echo(
            i18n._("plugin.install_dry_run", plugin_name=plugin_name, source_for_pip=source_for_pip)
        )
        return

    pip_cmd = _pip_cmd()
    try:
        subprocess.run(
            [*pip_cmd, "install", "--quiet", source_for_pip],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise PluginError(i18n._("plugin.install_failed", plugin_name=plugin_name, exc=exc)) from exc

    registry.add(
        PluginSpec(
            name=plugin_name,
            version=plugin_version,
            source=source_for_pip,
            entry_point=indexed.get("entry_point") if indexed else None,
            hooks=indexed.get("hooks", []) if indexed else [],
            trust_level=plugin_trust,
        )
    )
    typer.echo(i18n._("plugin.installed", plugin_name=plugin_name))


@app.command("uninstall")
def uninstall(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Name of the plugin to uninstall"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions without executing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmations"),
) -> None:
    """Uninstall a plugin package and remove it from the local registry."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = PluginRegistry()

    if not registry.get(name):
        raise PluginError(i18n._("plugin.not_registered", name=name))

    if not dry_run and not yes and not typer.confirm(i18n._("plugin.uninstall_confirm", name=name)):
        typer.echo(i18n._("common.aborted"))
        raise typer.Exit(code=0)

    if dry_run:
        typer.echo(i18n._("plugin.uninstall_dry_run", name=name))
        return

    pip_cmd = _pip_cmd()
    try:
        subprocess.run(
            [*pip_cmd, "uninstall", "--quiet", "-y", name],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise PluginError(i18n._("plugin.uninstall_failed", name=name, exc=exc)) from exc

    registry.remove(name)
    typer.echo(i18n._("plugin.uninstalled", name=name))


@app.command("trust")
def trust(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Name of the plugin"),
    level: TrustLevel = typer.Argument(..., help="New trust level"),
) -> None:
    """Update the trust level of a registered plugin."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = PluginRegistry()
    if not registry.trust(name, level):
        raise PluginError(i18n._("plugin.not_registered", name=name))
    typer.echo(i18n._("plugin.trust_set", name=name, level=level.value))
