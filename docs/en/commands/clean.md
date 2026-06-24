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
- When external tools such as `autoflake` / `black` are not available, clean falls back to a built-in formatter automatically.

## Built-in Formatter

When the external toolchain is incomplete, clean uses a built-in formatter that handles the following file types:

`.py` `.pyi` `.pyx` `.pxd` `.js` `.ts` `.jsx` `.tsx` `.rs` `.go` `.java` `.c` `.cpp` `.h` `.rb`

Formatting scope:
- Strip trailing whitespace from each line
- Collapse multiple consecutive blank lines into a single blank line
- Compress runs of 2+ inline spaces into a single space (preserving indentation and string literals)
- Ensure the file ends with exactly one trailing newline

## Related Commands

- [verify](./verify.md) — Run verification commands
- [commit](./commit.md) — Commit changes
