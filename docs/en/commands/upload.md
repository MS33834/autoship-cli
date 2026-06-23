# upload

Upload artifacts to a configured target.

## Syntax

```bash
autoship upload [OPTIONS]
```

## Arguments

`upload` does not accept positional arguments.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--target TEXT` | required | Upload target: `pypi`, `docker`, or `github` |
| - | `--image TEXT` | - | Docker image name |
| `-t` | `--tag TEXT` | - | Docker image tag or GitHub release tag |
| - | `--artifact TEXT` | - | Artifacts to upload; can be repeated |
| - | `--repository TEXT` | `testpypi` | PyPI repository name |
| - | `--repository-url TEXT` | - | PyPI repository upload URL |
| - | `--registry TEXT` | - | Docker registry prefix, e.g. `localhost:5000` |

## Examples

Upload to PyPI (defaults to TestPyPI):

```bash
autoship upload --target pypi
```

Upload a Docker image:

```bash
autoship upload --target docker --image myapp --tag 0.1.0
```

Upload to a local Docker registry:

```bash
autoship upload --target docker --image myapp --tag 0.1.0 --registry localhost:5000
```

Preview without uploading:

```bash
autoship --dry-run upload --target pypi
```

## Output Notes / Common Errors

- Use `--repository-url` to override the default PyPI/TestPyPI endpoint.
- `--artifact` can be specified multiple times for GitHub releases.

## Related Commands

- [verify](./verify.md) — Verify before uploading
- [plugin](./plugin.md) — Manage upload-related plugins
