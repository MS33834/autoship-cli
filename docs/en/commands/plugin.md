# plugin

Manage plugins.

## Syntax

```bash
autoship plugin [OPTIONS] COMMAND [ARGS]...
```

## Arguments

`plugin` does not accept positional arguments; use subcommands.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--help` | - | Show help and exit |

## Subcommands

### plugin list

List registered plugins and their trust levels. The output includes a tip to run `autoship plugin search` to browse all available plugins in the registry.

```bash
autoship plugin list
```

### plugin search

Search the official plugin registry index.

```bash
autoship plugin search [OPTIONS] [KEYWORD]
```

| Name | Required | Description |
|---|---|---|
| `keyword` | No | Keyword to search in plugin names or descriptions |

### plugin info

Show detailed information about a plugin in the registry.

```bash
autoship plugin info [OPTIONS] NAME
```

| Name | Required | Description |
|---|---|---|
| `name` | Yes | Plugin name |

### plugin install

Install a plugin package and register it locally.

```bash
autoship plugin install [OPTIONS] SOURCE
```

| Name | Required | Description |
|---|---|---|
| `source` | Yes | Package spec or plugin name from the registry |

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--name TEXT` | - | Plugin name to register |
| - | `--version TEXT` | - | Plugin version |
| - | `--trust LEVEL` | - | Initial trust level: `builtin`, `verified`, `community`, `untrusted` |
| - | `--dry-run` | `False` | Preview actions |
| `-y` | `--yes` | `False` | Skip confirmations |
| - | `--skip-trust-check` | `False` | Skip trust-level warnings |
| - | `--no-sandbox` | `False` | Run pip install without sandbox |

### plugin uninstall

Uninstall a plugin package and remove it from the local registry.

```bash
autoship plugin uninstall [OPTIONS] NAME
```

| Name | Required | Description |
|---|---|---|
| `name` | Yes | Plugin name to uninstall |

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--dry-run` | `False` | Preview actions |
| `-y` | `--yes` | `False` | Skip confirmations |

### plugin rate

Rate a registered plugin.

```bash
autoship plugin rate [OPTIONS] NAME SCORE
```

| Name | Required | Description |
|---|---|---|
| `name` | Yes | Plugin name |
| `score` | Yes | Rating from 1 to 5 |

### plugin stats

Show local plugin usage statistics.

```bash
autoship plugin stats
```

### plugin trust

Update the trust level of a registered plugin.

```bash
autoship plugin trust [OPTIONS] NAME LEVEL
```

| Name | Required | Description |
|---|---|---|
| `name` | Yes | Plugin name |
| `level` | Yes | New trust level: `builtin`, `verified`, `community`, `untrusted` |

### plugin update

Check for and install plugin updates.

```bash
autoship plugin update [OPTIONS] [NAME]
```

| Name | Required | Description |
|---|---|---|
| `name` | No | Plugin name to update |

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--all` | `False` | Update all registered plugins |
| - | `--dry-run` | `False` | Preview actions |
| `-y` | `--yes` | `False` | Skip confirmations |
| - | `--skip-trust-check` | `False` | Skip trust-level warnings |
| - | `--no-sandbox` | `False` | Run pip install without sandbox |

## Examples

List registered plugins:

```bash
autoship plugin list
```

Search the registry:

```bash
autoship plugin search docker
```

Show plugin details:

```bash
autoship plugin info docker-ship
```

Install a registry plugin:

```bash
autoship plugin install docker-ship
```

Install a local plugin with a trust level:

```bash
autoship plugin install ./local-plugin --trust verified
```

Update trust level:

```bash
autoship plugin trust my-plugin verified
```

Uninstall a plugin:

```bash
autoship plugin uninstall my-plugin
```

Update all plugins:

```bash
autoship plugin update --all
```

## Output Notes / Common Errors

- Trust levels: `builtin` > `verified` > `community` > `untrusted`.
- Installing an unverified plugin shows a trust warning; use `--skip-trust-check` to bypass.
- `--no-sandbox` disables the pip install sandbox; only use it in trusted environments.

## Related Commands

- [registry](./registry.md) — Browse and sync the plugin registry
- [doctor](./doctor.md) — Check plugin external dependencies
