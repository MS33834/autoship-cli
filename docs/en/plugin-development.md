---
title: Plugin Development Guide
---
# Plugin Development Guide

AutoShip-CLI's plugin system is based on [pluggy](https://pluggy.readthedocs.io/). You only need to implement the hooks defined in `autoship.hookspec.AutoShipHookSpec` and register the plugin object to the `autoship.plugins` entry point.

> We recommend using [`autoship-sdk`](https://pypi.org/project/autoship-sdk/) to simplify plugin development.
> It provides base classes, decorators, and testing utilities.

## Using autoship-sdk (Recommended)

Install the SDK:

```bash
pip install autoship-sdk
```

Minimal plugin example:

```python
from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class MyPlugin(Plugin):
    @hook
    def pre_commit(self, context: CommandContext) -> None:
        print(f"About to commit in {context.project_root}")
```

Register it via `pyproject.toml`:

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin.plugin:MyPlugin"
```

### Testing Plugins

`PluginTestHarness` provides an isolated hook invocation environment:

```python
from autoship_sdk.testing import PluginTestHarness
from my_plugin.plugin import MyPlugin


def test_pre_commit():
    harness = PluginTestHarness()
    harness.register(MyPlugin())
    ctx = harness.make_context("commit")
    results = harness.call("pre_commit", ctx)
    assert results == [None]
```

### Project Scaffolding

```python
from autoship_sdk import create_plugin
from pathlib import Path

create_plugin(
    target_dir=Path("./autoship-my-plugin"),
    plugin_name="my-plugin",
    description="My first AutoShip plugin",
)
```

This generates a complete project with `pyproject.toml`, `README.md`, plugin source code, and a test structure.

## CommandContext

All hooks receive an immutable `CommandContext`:

```python
@dataclass(frozen=True)
class CommandContext:
    command: str              # Current command name, e.g. "verify"
    project_root: Path        # Project root directory
    config: AppConfig         # Loaded configuration object
    verbose: bool = False     # Whether verbose output is enabled
    dry_run: bool = False     # Whether to only preview
    yes: bool = False         # Whether to skip confirmations
    trace_id: str = ""        # Audit trace ID
    extras: dict[str, Any] = field(default_factory=dict)  # Extra command parameters
```

Commands can pass extra information to hooks via `extras`. For example, the `verify` command passes `{"verify_command": ..., "fix": ...}`.

## Minimal Plugin Example

Create `my_plugin.py`:

```python
from autoship.core.context import CommandContext
from autoship.hookspec import hookimpl


class MyPlugin:
    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        print(f"About to commit in {context.project_root}")


plugin = MyPlugin()
```

## Registering via entry_points

It is recommended to package the plugin as a standalone Python package and register it via `pyproject.toml`:

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin:plugin"
```

Here `my_plugin:plugin` points to the plugin object containing the hook methods. You can also point to a factory function that returns a plugin object:

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin.plugin:register"
```

```python
def register():
    return MyPlugin()
```

AutoShip automatically discovers and loads all `autoship.plugins` entry points at startup.

## Complete Example: on_error Fix Suggestion

The following plugin returns a fix suggestion when `verify --fix` fails:

```python
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.hookspec import hookimpl


class FixOnVerifyPlugin:
    @hookimpl
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        if context.command != "verify":
            return None

        message = str(error)
        if "ImportError" not in message:
            return None

        return FixSuggestion(
            description="Missing dependency detected; run `uv pip install -e .`",
            patch="",
        )


plugin = FixOnVerifyPlugin()
```

## Installation & Verification

1. Install the plugin package:

```bash
pip install -e .
```

2. Check whether the plugin is loaded:

```bash
autoship --verbose verify pytest
```

3. Run unit tests (see this repository's `examples/custom-plugin`).

## Repository Example

See [`examples/custom-plugin`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin). This example implements:

- `pre_commit`: Scans the project root for a `TODO` file and warns before committing.
- `on_error`: Returns a `FixSuggestion` when `verify` fails and the user enabled `--fix`.

## Best Practices

- **Only catch exceptions you care about**: In `on_error`, do not swallow critical exceptions; return `None` to let other plugins handle them.
- **Avoid side effects**: `pre_*` / `post_*` hooks should be lightweight; complex operations should run asynchronously or in a subprocess.
- **Respect `dry_run` and `yes`**: Check these two flags before modifying the file system or remote state.
- **Do not leak sensitive information**: When reading credentials from `context.config`, avoid printing them to logs.
- **Use type annotations**: This facilitates static checking (pyright / mypy) and stays consistent with the core code.

## Complete Example: Custom Verification Plugin

The following uses a "sensitive file check plugin before commit" as an example to demonstrate how to develop, test, and install an AutoShip plugin from scratch. The plugin uses `autoship-sdk` and scans the project root directory during the `pre_commit` phase. If sensitive files such as `.env` or `secrets.json` are found, it blocks the commit with a clear message.

### Project Structure

```text
autoship-no-secret-plugin/
├── pyproject.toml
├── README.md
└── src/
    └── autoship_no_secret_plugin/
        ├── __init__.py
        └── plugin.py
```

A `src` layout is recommended to avoid accidentally importing the source directory at runtime and to make it easier for packaging tools (hatchling, setuptools, etc.) to resolve package paths correctly.

### pyproject.toml Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "autoship-no-secret-plugin"
version = "0.1.0"
description = "Block commits when common secret files are present"
requires-python = ">=3.10"
dependencies = [
    "autoship>=0.2.0b1",
    "autoship-sdk>=0.1.0b1",
]

[project.entry-points."autoship.plugins"]
no_secret = "autoship_no_secret_plugin.plugin:register"
```

Notes:

- `[build-system]` uses `hatchling`, which is lightweight and requires no extra `MANIFEST.in`.
- `[project.entry-points."autoship.plugins"]` registers the plugin into AutoShip's plugin namespace; `no_secret` is the plugin ID, and `autoship_no_secret_plugin.plugin:register` points to the factory function.
- Both `autoship` and `autoship-sdk` are declared as dependencies — the former for types and runtime compatibility, the latter for the `Plugin` base class and `hook` decorator.

### Plugin Code

`src/autoship_no_secret_plugin/__init__.py`:

```python
"""AutoShip plugin that prevents accidental commits of secret files."""
```

`src/autoship_no_secret_plugin/plugin.py`:

```python
from __future__ import annotations

from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class NoSecretPlugin(Plugin):
    """Scan the project root for sensitive files before each commit."""

    SENSITIVE_PATTERNS = (".env", "secrets.json", "credentials.json")

    @hook
    def pre_commit(self, context: CommandContext) -> None:
        """Raise an error if a sensitive file is found in the project root."""
        # In dry-run mode, only warn without blocking the actual workflow
        if context.dry_run:
            return

        for name in self.SENSITIVE_PATTERNS:
            path = context.project_root / name
            if path.exists():
                raise RuntimeError(
                    f"[no-secret-plugin] Blocked commit: sensitive file "
                    f"'{path.name}' exists. Add it to .gitignore or remove it."
                )


def register() -> NoSecretPlugin:
    """Factory used by the ``autoship.plugins`` entry point."""
    return NoSecretPlugin()
```

Key points:

- Inheriting from `autoship_sdk.Plugin` and using `@hook` to register hooks is more concise than working with `hookimpl` directly.
- Use `context.project_root` to locate files instead of `Path.cwd()`, ensuring the check works correctly even when `autoship commit` is run from a subdirectory.
- Check `context.dry_run` to avoid raising exceptions in preview mode; for blocking checks, dry-run should typically be skipped silently.
- Use a concrete exception type (such as `RuntimeError`) rather than `SystemExit` so that AutoShip's error handling and audit logs can capture and display it.

### Test Example

Create `tests/test_plugin.py` in the plugin directory:

```python
import pytest
from autoship_sdk.testing import PluginTestHarness

from autoship_no_secret_plugin.plugin import NoSecretPlugin


def test_pre_commit_allows_clean_project():
    harness = PluginTestHarness()
    harness.register(NoSecretPlugin())
    ctx = harness.make_context("commit")
    results = harness.call("pre_commit", ctx)
    assert results == [None]


def test_pre_commit_blocks_secret_file():
    harness = PluginTestHarness()
    harness.register(NoSecretPlugin())
    ctx = harness.make_context("commit")

    # The project_root provided by PluginTestHarness is a temporary directory
    secret = ctx.project_root / ".env"
    secret.write_text("SECRET=1\n")

    with pytest.raises(RuntimeError, match=".env"):
        harness.call("pre_commit", ctx)
```

Testing strategy:

- The positive case confirms the plugin does not raise an error when no sensitive files are present.
- The negative case writes a `.env` file into the `project_root` temporary directory and verifies the plugin raises an exception containing the file name.
- Use `PluginTestHarness` to isolate the hook invocation environment and avoid affecting real projects.

Run the tests:

```bash
cd autoship-no-secret-plugin
pytest
```

### Installation & Verification

1. Install the plugin in editable mode:

    ```bash
    cd autoship-no-secret-plugin
    pip install -e .
    ```

2. Check whether AutoShip has loaded the plugin:

    ```bash
    autoship --verbose plugin list
    ```

    You should see output similar to:

    ```text
    Name              Version    Trust        Source
    ----------------- ---------- ------------ -------------------------------
    builtin           0.2.0      builtin      autoship.builtin
    no_secret         0.1.0      community    autoship_no_secret_plugin
    ```

3. Test dry-run mode in any project:

    ```bash
    autoship commit --dry-run
    ```

    Since the plugin returns directly under `dry_run`, it will not block.

4. Trigger a real block:

    ```bash
    touch .env
    autoship commit
    ```

    AutoShip is expected to catch the exception during the `pre_commit` phase and display:

    ```text
    [no-secret-plugin] Blocked commit: sensitive file '.env' exists.
    Add it to .gitignore or remove it.
    ```

5. Commit again after cleanup:

    ```bash
    rm .env
    autoship commit
    ```

### Relationship with the Repository Example

This repository's [`examples/custom-plugin/`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin) also implements `pre_commit` (checking for a `TODO` file) and `on_error` (returning a `FixSuggestion`). The only difference between the two is the business logic:

- `custom-plugin` is suitable for learning how to provide fix suggestions on failure.
- The `no-secret-plugin` in this section is suitable for learning how to perform lightweight pre-checks, respect `dry_run`, use concrete exceptions, and stay project-path independent.

When developing plugins, we recommend using the `Plugin` + `@hook` pattern from `autoship-sdk` first; if you only need a simple functional plugin, consider using `hookimpl` directly.
