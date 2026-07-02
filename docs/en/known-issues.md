---
title: Known Issues
---
# Known Issues

> This page honestly records AutoShip's current known limitations and unresolved issues, so you can assess whether they affect your usage. Issues marked "planned fix" will be addressed in a future release.

## `verify --fix` Unavailable Without an AI Backend

`verify --fix` depends on an AI model to generate fix suggestions. If no model backend is configured (neither local Ollama nor a cloud provider), the subcommand exits with an error and does **not** silently fall back to template-based fixes.

- Workaround: use `autoship verify pytest` (without `--fix`) for verification only;
- Or configure Ollama following the "+5-Minute AI Version" in the [Quickstart](quickstart.md).
- Status: by design, not a bug.

## Windows Path Edge Cases

Several known path issues exist on Windows:

- User directories containing spaces or non-ASCII characters (e.g. `C:\Users\Zhang San\`) may cause audit-log path resolution anomalies;
- `upload --target docker` does not fully support `\\wsl$\` paths on PowerShell versions below 7;
- Backslash paths in `.autoship.toml` must be escaped or replaced with forward slashes.

Status: unified path handling is planned for the 1.1 release.

## `clean` Performance on Large Repositories

On large repositories with roughly 50k+ files, `clean`'s full scan may take tens of seconds and memory usage can be high.

- Workaround: configure `clean.exclude` in `.autoship.toml` to skip `node_modules`, `venv`, build outputs, etc.;
- Or use `clean --paths src/` to limit the scan scope.
- Status: incremental scanning and parallelization are on the roadmap.

## Translations May Lag

Chinese is the source language; English and Japanese are translations. New features or revisions may land in the Chinese docs first, with an en/ja lag ranging from hours to a few days.

- Impact: for a short window after a release, en/ja docs may not yet reflect the latest commands or options.
- Status: CI now includes an i18n completeness check that warns on missing translations; mike versioned docs will enforce this more strictly once enabled.

## mike Versioned Docs to Be Enabled After 1.0

`mkdocs.yml` already declares `version.provider: mike`, but the version switcher is not yet officially enabled. All visitors currently see the latest build and cannot switch to historical versions.

- Status: mike subdomain and version selector will be enabled after the 1.0 release;
- In the meantime, to view historical docs, browse the `docs/` directory at the relevant tag on GitHub.

## Feedback & Tracking

If you hit a new issue not listed above, please:

- See [Troubleshooting](troubleshooting.md);
- Search or open an issue on [GitHub Issues](https://github.com/MS33834/autoship-cli/issues), attaching the `autoship doctor` output and `--verbose` logs.
