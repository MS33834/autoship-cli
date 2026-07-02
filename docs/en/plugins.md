---
title: Plugins
---
# Plugins

AutoShip-CLI uses [pluggy](https://pluggy.readthedocs.io/) to implement its plugin architecture. Plugins extend command behavior by declaring lifecycle hooks — for example, running extra checks before `verify`, or providing AI fix suggestions when a command fails.

## Built-in Official Plugins

### security-scan

Runs security checks such as `bandit`/`gitleaks`/`osv-scanner` during the `pre_commit` phase, blocking the commit when an issue reaches the threshold.

```toml
[security]
enabled = true
tools = ["bandit"]
threshold = "medium"
fail_fast = true
```

```bash
autoship commit
# If security-scan finds medium or higher severity issues, the commit is aborted
```

### docker-ship

Automatically builds/pushes Docker images before and after `autoship upload --target docker`.

```toml
[docker_ship]
enabled = true
default_image = "myapp"
default_tag = "latest"
push = true
```

```bash
autoship upload --target docker --image myapp --tag 0.1.0
```

### web-search

When `verify --fix` fails and `web_search.enabled = true` is set in the configuration, it searches the web for error context and helps generate fix suggestions. Disabled by default.

```toml
[web_search]
enabled = true
provider = "duckduckgo"
max_results = 3
```

```bash
autoship verify pytest --fix
```

!!! warning "Privacy Notice"
    When `web-search` is enabled, error summaries are sent to a public search service. Make sure you are willing to share this information before enabling it.

## Plugin Management CLI

AutoShip has built-in plugin management commands for viewing, installing, and configuring third-party plugins:

```bash
# List registered plugins
autoship plugin list

# Install a plugin (supports PyPI package names, local paths, or git URLs)
autoship plugin install my-plugin

# Adjust a plugin's trust level
autoship plugin trust my-plugin verified

# Uninstall a plugin
autoship plugin uninstall my-plugin
```

Trust levels are: `builtin`, `verified`, `community`, `untrusted`. Third-party plugins installed by default are `community`; we recommend only promoting them to `verified` after reviewing the source code.

## Available Hooks

All hooks are defined in `autoship.hookspec.AutoShipHookSpec`:

| Hook Name | Trigger Timing | Return Value |
|---|---|---|
| `pre_init` | Before `autoship init` writes the configuration file | `None` |
| `post_init` | After `autoship init` writes the configuration file | `None` |
| `pre_clean` | Before `autoship clean` runs cleanup tools | `None` |
| `post_clean` | After `autoship clean` runs cleanup tools | `None` |
| `pre_commit` | Before `autoship commit` generates the commit message | `None` |
| `post_commit` | After `autoship commit` completes | `None` |
| `pre_verify` | Before `autoship verify` runs the verification command | `None` |
| `post_verify` | After `autoship verify` completes | `None` |
| `pre_upload` | Before `autoship upload` publishes artifacts | `None` |
| `post_upload` | After `autoship upload` completes | `None` |
| `on_error` | When a command execution throws an exception | `FixSuggestion \| None` |

`on_error` is the only hook allowed to return a value. When a command with the `--fix` flag fails, AutoShip collects all `FixSuggestion`s, displays them to the user, and optionally applies patches.

## Developing Custom Plugins

See the [Plugin Development Guide](plugin-development.md) to learn how to create, package, register, and test your own plugins.
