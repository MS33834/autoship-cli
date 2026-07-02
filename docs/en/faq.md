---
title: FAQ
---
# Frequently Asked Questions (FAQ)

## General

### Does AutoShip upload my code?

No. By default, all core processing (cleanup, verification, commit message generation) is done locally. Only when you explicitly configure an external model backend (such as OpenAI) or an upload target (PyPI, Docker Registry) will the necessary data be sent to the corresponding service. See the [Privacy Policy](privacy.md) for details.

### Does using AutoShip require an internet connection?

Core commands (`init`, `clean`, `commit`, `verify`) can run in a fully offline environment. Features that require an internet connection include:

- `upload` to PyPI / Docker / GitHub
- The `web-search` plugin's online search
- `plugin install` to install plugins from PyPI or a remote registry
- Using cloud model backends

### Which operating systems does AutoShip support?

AutoShip runs on Linux, macOS, and Windows. CI also builds binaries for all three platforms. The recommended Python version is 3.10 or above.

## Installation & Upgrade

### How do I install AutoShip?

Recommended methods:

```bash
pipx install autoship
```

Or use uv:

```bash
uv tool install autoship
```

Developers can clone the repository and install with `uv sync --all-extras --dev`.

### How do I upgrade to the latest version?

```bash
pipx upgrade autoship
# or
pip install --upgrade autoship
```

### What if the `autoship` command is not found?

1. Confirm the installation succeeded: `pipx list` or `pip show autoship`.
2. Check whether PATH includes the pipx / Python scripts directory.
3. If using a virtual environment, make sure it is activated.

## Models & AI

### Can I use cloud models like OpenAI / Claude / Azure?

Yes. Configure the corresponding provider in `.autoship.toml` under `[model.backends]`, for example `openai`, `azure_openai`, `openrouter`. We recommend injecting the API key via environment variables rather than writing it into the configuration file.

```toml
[[model.backends]]
provider = "openai"
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key = "${OPENAI_API_KEY}"
```

### What do you recommend for local models?

- [Ollama](https://ollama.com/): The easiest way to get started, supports many open-source models.
- [LM Studio](https://lmstudio.ai/): Has a graphical interface, suitable for local experimentation.
- [llama.cpp](https://github.com/ggerganov/llama.cpp) or [vLLM](https://github.com/vllm-project/vllm): Suitable for advanced users with GPUs.

See [Model Configuration](models.md) for details.

### What should I do if the model backend connection fails?

1. Run `autoship doctor` to check the model backend status.
2. Confirm the backend service is running and `base_url` is correct.
3. Check firewall or proxy settings.
4. View logs: `autoship --verbose <command>`.

## Configuration

### Where is the configuration file located?

Project-level configuration: `.autoship.toml` (project root directory).

Team-level configuration: `.autoship.team.toml` (project root directory, can be overridden by project configuration).

Global configuration:

- Linux/macOS: `~/.config/autoship/config.toml`
- Windows: `%APPDATA%\autoship\config.toml`

### How do I disable telemetry?

Telemetry is disabled by default. To confirm explicitly:

```toml
[telemetry]
enabled = false
```

### How do I switch languages?

```bash
autoship --lang en <command>
# or in configuration
locale = "en"
```

## Plugins

### How do I install a third-party plugin?

```bash
autoship plugin install my-plugin
```

After installation, it defaults to the `community` trust level. After reviewing the source code, you can promote it to `verified`:

```bash
autoship plugin trust my-plugin verified
```

### How do I develop my own plugin?

See the [Plugin Development Guide](plugin-development.md) and the example plugin [`examples/custom-plugin`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin).

### Can plugins execute system commands?

Yes, but you must declare `shell = true` in `permissions` and obtain user confirmation. We recommend following the principle of least privilege.

## Security & Audit

### How does AutoShip protect my credentials?

- Audit logs and error logs mask sensitive information such as API keys, tokens, and passwords by default.
- We recommend injecting keys via environment variables rather than writing them into configuration files.
- Configuration file permissions are automatically set to owner-only read/write by the system.

### How long are audit logs retained?

Retained for 30 days by default. Configurable via `.autoship.toml`:

```toml
[audit]
retention_days = 30
```

Manual cleanup:

```bash
autoship audit cleanup
```

### How do I report a security vulnerability?

Please report it privately via email to `security@autoship.dev` instead of creating a public issue. See the [Security Policy](security.md) for details.

## Troubleshooting

### `autoship verify` fails but the tests themselves are fine?

The `verify` command first runs the test/check command you specify, then runs AutoShip's verification flow. Please check:

1. Whether the invoked test command itself passes.
2. Whether any plugin failed during the `pre_verify` / `post_verify` phase.
3. Use `--verbose` to view detailed logs.

### Not satisfied with the message generated by `autoship commit`?

You can use `--edit` to open the editor and modify the generated message, or adjust `commit.max_tokens` and `conventional_commits` in the configuration.

### How do I reset the AutoShip configuration?

Delete `.autoship.toml` in the project root directory and run `autoship init` again.

## Quickstart-related

### Why does `verify --fix` in the Quickstart report "no AI backend configured"?

`verify --fix` requires an available AI model to generate fix suggestions. The "5-Minute No-AI Version" of the Quickstart does not configure any model backend, so calling `verify --fix` directly raises "no AI backend configured".

- To verify without fixing: use `autoship verify pytest` (without `--fix`);
- To try the fix flow: configure Ollama following the "+5-Minute AI Version" in the [Quickstart](quickstart.md).
- This is by design, not a bug. See [Known Issues](known-issues.md).

### After finishing the Quickstart, how do I configure full AI features?

1. Install and start [Ollama](https://ollama.com/);
2. Pull a model: `ollama pull qwen2.5-coder:1.5b` (or a larger one);
3. Configure the `[model]` section in `.autoship.toml` with `backend = "ollama"`;
4. Run `autoship doctor` to confirm the backend is reachable;
5. Try `autoship verify --fix pytest` and `autoship commit` (AI-generated message).

For the full set of options (including cloud models), see [Model Configuration](models.md).

### How do I choose a model?

Choose by scenario:

- **Beginner / low-spec machine**: local Ollama + `qwen2.5-coder:1.5b` or `phi3:mini` — fast and low VRAM.
- **High-quality local**: `qwen2.5-coder:7b`, `deepseek-coder:6.7b` — needs 8GB+ VRAM.
- **High-quality cloud**: OpenAI `gpt-4o-mini` / `gpt-4o`, Anthropic Claude, Azure OpenAI — needs network and API key.
- **Privacy-first**: always use local models; never configure a cloud provider.

See the selection table in [Model Configuration](models.md).

### Troubleshooting plugin installation failures

When `autoship plugin install <name>` fails, investigate in this order:

1. Network: can you reach PyPI? Does `pip install <name>` succeed?
2. Trust level: unreviewed plugins need confirmation or an explicit `autoship plugin trust <name> community`;
3. Permissions: if the plugin declares `shell = true`, you must allow it in the interactive confirmation;
4. Compatibility: does the plugin's declared AutoShip version range cover your current version (`autoship --version`)?
5. Logs: `autoship --verbose plugin install <name>` for detailed errors.

See [Troubleshooting](troubleshooting.md).

### Three-language documentation sync strategy

- **Source language**: Chinese (zh) is the source; en/ja are translations;
- **Sync window**: new content lands in zh first; en/ja typically follow within hours to a few days;
- **CI check**: the i18n completeness check compares the file lists across the three languages and warns on missing pages or entries;
- **Command code blocks are not translated**: shell / toml / yaml code blocks stay in English across all three languages; only comments and prose are localized;
- **Relative links**: cross-page links use relative paths and the three-language directory structure stays consistent (`docs/`, `docs/en/`, `docs/ja/`).

If you notice translation lag or gaps, please open an issue at [GitHub Issues](https://github.com/MS33834/autoship-cli/issues).
