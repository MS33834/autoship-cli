"""The ``autoship plugin`` command."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

import typer
from packaging.version import Version
from packaging.version import parse as parse_version

from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.plugin_registry import CapabilityManifest, PluginRegistry, PluginSpec, TrustLevel
from autoship.core.plugin_stats import PluginStats
from autoship.core.registry_index import RegistryIndex
from autoship.core.sandbox import SandboxRunner
from autoship.exceptions import PluginError

app = typer.Typer()


def _pip_cmd() -> list[str]:
    """Return the preferred package installer command (uv or pip)."""
    if shutil.which("uv"):
        return ["uv", "pip"]
    return ["pip"]


def _run_pip_install(
    pip_cmd: list[str],
    spec: str,
    *,
    upgrade: bool = False,
    sandbox: bool = True,
    env_whitelist: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run pip install, optionally inside a sandbox for untrusted plugins."""
    args = [*pip_cmd, "install", "--quiet"]
    if upgrade:
        args.append("--upgrade")
    args.append(spec)

    if sandbox:
        runner = SandboxRunner(
            network=True,
            env_whitelist=env_whitelist or ["PATH", "HOME", "USER", "LANG", "LC_ALL", "PIP_INDEX_URL"],
        )
        result = runner.run(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return subprocess.run(args, check=True, capture_output=True, text=True)


def _installed_version(package: str) -> Version | None:
    """Return the installed version of a package, or None if not installed."""
    pip_cmd = _pip_cmd()
    try:
        result = subprocess.run(
            [*pip_cmd, "show", package],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None

    match = re.search(r"^Version:\s*(\S+)", result.stdout, re.MULTILINE)
    if not match:
        return None
    try:
        return parse_version(match.group(1))
    except Exception:  # noqa: BLE001
        return None


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


def _publisher_badge(plugin: dict[str, Any]) -> str:
    publisher = plugin.get("publisher")
    if not publisher:
        return ""
    verified = publisher.get("verified")
    badge = "✓ verified" if verified else "unverified"
    return f"{publisher.get('id', '?')} ({badge})"


def _capabilities_from_index(indexed: dict[str, Any] | None) -> dict[str, Any]:
    """Build capability kwargs from registry entry permissions/capabilities."""
    if not indexed:
        return {}
    permissions = cast(dict[str, Any], indexed.get("permissions") or indexed.get("capabilities") or {})
    return {
        "filesystem": permissions.get("filesystem", "read-only"),
        "network": permissions.get("network", False),
        "shell": permissions.get("shell", False),
        "git": permissions.get("git", False),
        "env": permissions.get("env", []),
    }


def _format_capabilities(capabilities: CapabilityManifest) -> str:
    """Return a concise, human-readable capability summary."""
    return ", ".join(capabilities.summary()) or "none"


@app.command("search")
def search_plugins(
    ctx: typer.Context,
    keyword: str | None = typer.Argument(None, help="Keyword to search in name or description"),
) -> None:
    """Search the official plugin registry index."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    index = RegistryIndex(ctx.obj.get("config"))
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


@app.command("info")
def info(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Plugin name"),
) -> None:
    """Show detailed information about a plugin in the registry."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    index = RegistryIndex(ctx.obj.get("config"))
    plugin = index.get(name)
    if plugin is None:
        raise PluginError(i18n._("plugin.not_found_in_registry", name=name))

    typer.echo(f"Name:        {plugin['name']}")
    typer.echo(f"Version:     {plugin.get('version', '?')}")
    typer.echo(f"Trust:       {plugin.get('trust_level', 'community')}")
    typer.echo(f"Publisher:   {_publisher_badge(plugin) or 'Unknown'}")
    typer.echo(f"Maintainer:  {plugin.get('maintainer', 'Unknown')}")
    typer.echo(f"License:     {plugin.get('license', 'Unknown')}")
    typer.echo(f"Categories:  {', '.join(plugin.get('categories', [])) or '—'}")
    typer.echo(f"Tags:        {', '.join(plugin.get('tags', [])) or '—'}")
    typer.echo(f"Permissions: {_format_capabilities(CapabilityManifest(**_capabilities_from_index(plugin)))}")
    typer.echo(f"Downloads:   {plugin.get('downloads', 0)}")
    rating = plugin.get("rating")
    rating_str = f"{rating['score']:.1f} / 5 ({rating['count']})" if rating and rating.get("count") else "—"
    typer.echo(f"Rating:      {rating_str}")
    if plugin.get("homepage"):
        typer.echo(f"Homepage:    {plugin['homepage']}")
    if plugin.get("source_url"):
        typer.echo(f"Source:      {plugin['source_url']}")
    typer.echo(f"Install:     autoship plugin install {plugin['name']}")


@app.command("install")
def install(
    ctx: typer.Context,
    source: str = typer.Argument(..., help="Package spec or plugin name from registry"),
    name: str | None = typer.Option(None, "--name", help="Plugin name to register"),
    version: str | None = typer.Option(None, "--version", help="Plugin version"),
    trust: TrustLevel | None = typer.Option(None, "--trust", help="Initial trust level"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions without executing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmations"),
    skip_trust_check: bool = typer.Option(False, "--skip-trust-check", help="Skip trust level warnings"),
    no_sandbox: bool = typer.Option(False, "--no-sandbox", help="Run pip install without sandbox"),
) -> None:
    """Install a plugin package and register it locally."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = PluginRegistry()
    index = RegistryIndex(ctx.obj.get("config"))
    indexed = index.get(source)

    if indexed:
        plugin_name = name or indexed["name"]
        package = indexed["package"]
        plugin_version = version or indexed.get("version", "0.0.0")
        plugin_trust = trust or TrustLevel(indexed.get("trust_level", "verified"))
        source_for_pip = package
        publisher = _publisher_badge(indexed)
        if publisher:
            typer.echo(f"Publisher: {publisher}")
    else:
        plugin_name = name or Path(source).name
        package = source
        plugin_version = version or "0.0.0"
        plugin_trust = trust or TrustLevel.COMMUNITY
        source_for_pip = source

    capabilities = CapabilityManifest(**_capabilities_from_index(indexed))

    if not dry_run:
        _confirm_trust(i18n, plugin_name, plugin_trust, indexed, capabilities, yes, skip_trust_check)

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

    use_sandbox = not no_sandbox and plugin_trust in (TrustLevel.COMMUNITY, TrustLevel.UNTRUSTED)

    pip_cmd = _pip_cmd()
    try:
        result = _run_pip_install(
            pip_cmd,
            source_for_pip,
            sandbox=use_sandbox,
            env_whitelist=capabilities.env + ["PATH", "HOME", "USER", "LANG", "LC_ALL", "PIP_INDEX_URL"],
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
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
            capabilities=capabilities,
            sha256=indexed.get("sha256") if indexed else None,
            signature=indexed.get("signature") if indexed else None,
            maintainer=indexed.get("maintainer") if indexed else None,
            license=indexed.get("license") if indexed else None,
        )
    )
    PluginStats().record_install(plugin_name)
    typer.echo(i18n._("plugin.installed", plugin_name=plugin_name))


def _confirm_trust(
    i18n: I18n,
    plugin_name: str,
    plugin_trust: TrustLevel,
    indexed: dict[str, Any] | None,
    capabilities: CapabilityManifest,
    yes: bool,
    skip_trust_check: bool,
) -> None:
    """Prompt the user when installing plugins that are not fully trusted."""
    if skip_trust_check or yes:
        return

    if plugin_trust in (TrustLevel.COMMUNITY, TrustLevel.UNTRUSTED):
        message_key = (
            "plugin.install_trust_warning_community"
            if plugin_trust == TrustLevel.COMMUNITY
            else "plugin.install_trust_warning_untrusted"
        )
        typer.echo(i18n._(message_key, plugin_name=plugin_name))
        typer.echo(
            i18n._(
                "plugin.install_permissions",
                permissions=_format_capabilities(capabilities),
            )
        )
        if not typer.confirm(i18n._("plugin.install_trust_confirm"), abort=False):
            typer.echo(i18n._("common.aborted"))
            raise typer.Exit(code=0)
        return

    if plugin_trust == TrustLevel.VERIFIED and indexed and not indexed.get("sha256") and not indexed.get("signature"):
        typer.echo(i18n._("plugin.install_unverified_signature", plugin_name=plugin_name))
        if not typer.confirm(i18n._("plugin.install_trust_confirm"), abort=False):
            typer.echo(i18n._("common.aborted"))
            raise typer.Exit(code=0)



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
    PluginStats().record_uninstall(name)
    typer.echo(i18n._("plugin.uninstalled", name=name))


@app.command("rate")
def rate(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Name of the plugin to rate"),
    score: float = typer.Argument(..., help="Rating from 1 to 5"),
) -> None:
    """Rate a registered plugin."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = PluginRegistry()
    if registry.get(name) is None:
        raise PluginError(i18n._("plugin.not_registered", name=name))
    try:
        PluginStats().record_rate(name, score)
    except ValueError as exc:
        raise PluginError(str(exc)) from exc
    typer.echo(i18n._("plugin.rated", name=name, score=score))


@app.command("stats")
def stats(
    ctx: typer.Context,
) -> None:
    """Show local plugin usage statistics."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    summary = PluginStats().summary()
    if not summary:
        typer.echo(i18n._("plugin.no_stats"))
        return

    typer.echo(
        f"{'Name':<30} {'Installs':<10} {'Uninstalls':<12} {'Rating':<15}"
    )
    for name, data in summary.items():
        rating = data["rating"]
        rating_str = f"{rating['score']:.1f} ({rating['count']})" if rating["count"] else "—"
        typer.echo(
            f"{name:<30} {data['installs']:<10} {data['uninstalls']:<12} {rating_str:<15}"
        )


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


@app.command("update")
def update(
    ctx: typer.Context,
    name: str | None = typer.Argument(None, help="Plugin name to update"),
    all_plugins: bool = typer.Option(False, "--all", help="Update all registered plugins"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show actions without executing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive confirmations"),
    skip_trust_check: bool = typer.Option(False, "--skip-trust-check", help="Skip trust level warnings"),
    no_sandbox: bool = typer.Option(False, "--no-sandbox", help="Run pip install without sandbox"),
) -> None:
    """Check for and install plugin updates."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    registry = PluginRegistry()
    index = RegistryIndex(ctx.obj.get("config"))

    plugins = registry.list()
    if name:
        plugin = registry.get(name)
        if plugin is None:
            raise PluginError(i18n._("plugin.not_registered", name=name))
        candidates = [plugin]
    elif all_plugins:
        candidates = plugins
    else:
        raise PluginError(i18n._("plugin.update_name_or_all"))

    updatable: list[tuple[PluginSpec, Version, Version]] = []
    skipped: list[tuple[PluginSpec, str]] = []
    for plugin in candidates:
        if plugin.trust_level == TrustLevel.BUILTIN:
            skipped.append((plugin, i18n._("plugin.update_skip_builtin")))
            continue
        if not plugin.source or plugin.source.startswith((".", "/", "~")):
            skipped.append((plugin, i18n._("plugin.update_skip_local")))
            continue

        installed = _installed_version(plugin.source)
        if installed is None:
            skipped.append((plugin, i18n._("plugin.update_skip_not_installed")))
            continue

        indexed = index.get(plugin.name)
        latest_raw = indexed.get("version") if indexed else plugin.version
        try:
            latest = parse_version(latest_raw or plugin.version)
        except Exception:  # noqa: BLE001
            latest = parse_version(plugin.version)

        if latest > installed:
            updatable.append((plugin, installed, latest))
        else:
            skipped.append((plugin, i18n._("plugin.update_skip_latest", installed=installed, latest=latest)))

    if not updatable:
        typer.echo(i18n._("plugin.update_none"))
        for plugin, reason in skipped:
            typer.echo(f"  - {plugin.name}: {reason}")
        return

    typer.echo(i18n._("plugin.update_available_header"))
    for plugin, installed, latest in updatable:
        typer.echo(f"  - {plugin.name}: {installed} -> {latest}")

    if not dry_run and not yes and not typer.confirm(i18n._("plugin.update_confirm")):
        typer.echo(i18n._("common.aborted"))
        raise typer.Exit(code=0)

    pip_cmd = _pip_cmd()
    for plugin, _installed, latest in updatable:
        source_for_pip = plugin.source
        if dry_run:
            typer.echo(i18n._("plugin.update_dry_run", plugin_name=plugin.name, source_for_pip=source_for_pip))
            continue

        _confirm_trust(
            i18n,
            plugin.name,
            plugin.trust_level,
            index.get(plugin.name),
            plugin.capabilities,
            yes,
            skip_trust_check,
        )

        use_sandbox = not no_sandbox and plugin.trust_level in (TrustLevel.COMMUNITY, TrustLevel.UNTRUSTED)

        try:
            result = _run_pip_install(
                pip_cmd,
                source_for_pip,
                upgrade=True,
                sandbox=use_sandbox,
                env_whitelist=plugin.capabilities.env + ["PATH", "HOME", "USER", "LANG", "LC_ALL", "PIP_INDEX_URL"],
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
            raise PluginError(i18n._("plugin.update_failed", plugin_name=plugin.name, exc=exc)) from exc

        plugin.version = str(latest)
        registry.add(plugin)
        typer.echo(i18n._("plugin.updated", plugin_name=plugin.name, version=latest))

    if skipped:
        typer.echo(i18n._("plugin.update_skipped_header"))
        for plugin, reason in skipped:
            typer.echo(f"  - {plugin.name}: {reason}")
