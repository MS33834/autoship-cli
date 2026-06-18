"""The ``autoship plugin`` command."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from autoship.core.plugin_registry import PluginRegistry, PluginSpec, TrustLevel
from autoship.exceptions import PluginError

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="plugin")


@app.command("list")
def list_plugins() -> None:
    """List registered plugins and their trust levels."""
    registry = PluginRegistry()
    plugins = registry.list()
    if not plugins:
        typer.echo("No plugins registered.")
        return

    typer.echo(f"{'Name':<30} {'Version':<10} {'Trust':<12} {'Source'}")
    for plugin in plugins:
        typer.echo(
            f"{plugin.name:<30} {plugin.version:<10} {plugin.trust_level.value:<12} {plugin.source}"
        )


@app.command("install")
def install(
    source: str = typer.Argument(..., help="Package spec, e.g. my-plugin or ./local-plugin"),
    name: str | None = typer.Option(None, "--name", help="Plugin name to register"),
    version: str = typer.Option("0.0.0", "--version", help="Plugin version"),
    trust: TrustLevel = typer.Option(TrustLevel.COMMUNITY, "--trust", help="Initial trust level"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions without executing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmations"),
) -> None:
    """Install a plugin package and register it locally."""
    registry = PluginRegistry()
    plugin_name = name or Path(source).name

    if (
        not dry_run
        and not yes
        and not typer.confirm(f"Install plugin {plugin_name} from {source}?")
    ):
        typer.echo("Aborted.")
        raise typer.Exit(code=0)

    if dry_run:
        typer.echo(f"[dry-run] Would install {plugin_name} from {source}")
        return

    try:
        subprocess.run(
            ["pip", "install", "--quiet", source],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise PluginError(f"Failed to install plugin {plugin_name}: {exc}") from exc

    registry.add(
        PluginSpec(
            name=plugin_name,
            version=version,
            source=source,
            trust_level=trust,
        )
    )
    typer.echo(f"Installed plugin: {plugin_name}")


@app.command("uninstall")
def uninstall(
    name: str = typer.Argument(..., help="Name of the plugin to uninstall"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions without executing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmations"),
) -> None:
    """Uninstall a plugin package and remove it from the local registry."""
    registry = PluginRegistry()

    if not registry.get(name):
        raise PluginError(f"Plugin {name} is not registered")

    if not dry_run and not yes and not typer.confirm(f"Uninstall plugin {name}?"):
        typer.echo("Aborted.")
        raise typer.Exit(code=0)

    if dry_run:
        typer.echo(f"[dry-run] Would uninstall {name}")
        return

    try:
        subprocess.run(
            ["pip", "uninstall", "--quiet", "-y", name],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise PluginError(f"Failed to uninstall plugin {name}: {exc}") from exc

    registry.remove(name)
    typer.echo(f"Uninstalled plugin: {name}")


@app.command("trust")
def trust(
    name: str = typer.Argument(..., help="Name of the plugin"),
    level: TrustLevel = typer.Argument(..., help="New trust level"),
) -> None:
    """Update the trust level of a registered plugin."""
    registry = PluginRegistry()
    if not registry.trust(name, level):
        raise PluginError(f"Plugin {name} is not registered")
    typer.echo(f"Set trust level of {name} to {level.value}")
