# clean

Clean and format project code.

## Syntax

```bash
autoship clean [OPTIONS] [PATHS]...
```

## Arguments

| Name | Required | Description |
|---|---|---|
| `paths` | No | Paths to clean; defaults to current directory |

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--check` | `False` | Exit with error if changes are needed |
| `-y` | `--yes` | `False` | Skip interactive confirmations |

## Examples

Clean the current directory:

```bash
autoship clean
```

Clean specific paths:

```bash
autoship clean src tests
```

Check formatting in CI:

```bash
autoship clean --check
```

Skip confirmation:

```bash
autoship clean --yes
```

## Output Notes / Common Errors

- Default tool chain is `autoflake` and `black`; customize via `[clean]` in the config file.
- `--check` returns a non-zero exit code if any file would be reformatted.

## Related Commands

- [verify](./verify.md) — Run verification commands
- [commit](./commit.md) — Commit changes
