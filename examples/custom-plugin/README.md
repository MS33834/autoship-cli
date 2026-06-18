# AutoShip-CLI Custom Plugin Example

A minimal example plugin for AutoShip-CLI.

## Features

- `pre_commit`: warns if a `TODO` file exists in the project root.
- `on_error`: returns a `FixSuggestion` when `autoship verify --fix` fails.

## Install

```bash
cd examples/custom-plugin
pip install -e .
```

The `[project.entry-points."autoship.plugins"]` entry in `pyproject.toml`
registers the plugin with AutoShip automatically.

## Verify

```bash
# Create a TODO file to trigger the pre_commit warning
touch TODO
autoship commit -m "test"

# Trigger a verify failure with fix suggestions
autoship verify --fix false
```

## Test

```bash
pytest
```
