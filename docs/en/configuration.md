---
title: Configuration
---
# Configuration

AutoShip uses `.autoship.toml` as the project-level configuration file. Running `autoship init` creates a default configuration based on the project type and hardware.

## Full Example

```toml
# AutoShip configuration
schema_version = 1
project_type = "python"

[model]
default_tier = 2
fallback = true

[[model.backends]]
provider = "ollama"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen2.5:7b"
timeout = 30.0
concurrency = 2
priority = 0

[clean]
enabled = true
tools = ["autoflake", "black"]
exclude = ["migrations/"]

[commit]
enabled = true
max_tokens = 512
conventional_commits = true
auto_push = false

[security]
enabled = true
tools = ["bandit"]
threshold = "medium"
fail_fast = true

[web_search]
enabled = false
provider = "duckduckgo"
max_results = 3
timeout = 10.0

[docker_ship]
enabled = true
default_image = "myapp"
default_tag = "latest"
push = false
build_args = {}
```

## Configuration Options

### Top Level

| Field | Type | Default | Description |
|---|---|---|---|
| `schema_version` | int | `1` | Configuration file version |
| `project_type` | str | `"python"` | Project type, affects default templates |
| `log_level` | str | `"INFO"` | Log level |
| `telemetry_enabled` | bool | `false` | Whether telemetry is enabled |
| `audit_log_dir` | path | `null` | Audit log directory |

### `[model]` — Model Routing

| Field | Type | Default | Description |
|---|---|---|---|
| `default_tier` | 1/2/3 | `2` | Default model tier; higher numbers mean stronger capability |
| `fallback` | bool | `true` | Whether to fall back when the preferred backend fails |
| `backends` | array | `[]` | List of model backends |

#### `[[model.backends]]`

| Field | Type | Default | Description |
|---|---|---|---|
| `provider` | str | required | Backend type: `ollama`, `lm_studio`, `llama_cpp`, `vllm` |
| `base_url` | url | required | Backend API address |
| `api_key` | str | `null` | API key; injecting via environment variables is recommended |
| `model` | str | `null` | Model name |
| `timeout` | float | `30.0` | Request timeout (seconds) |
| `concurrency` | int | `2` | Concurrency |
| `priority` | int | `0` | Priority; higher values are preferred |

### `[clean]` — Code Cleanup

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Whether enabled |
| `tools` | array | `["autoflake", "black"]` | Formatting and cleanup tools |
| `exclude` | array | `[]` | Excluded paths |

### `[commit]` — Commit Generation

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Whether enabled |
| `max_tokens` | int | `512` | Maximum number of tokens for generating commit messages |
| `conventional_commits` | bool | `true` | Whether to generate Conventional Commits style |
| `auto_push` | bool | `false` | Whether to automatically push after committing |

### `[security]` — Security Scanning

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Whether enabled |
| `tools` | array | `["bandit"]` | Scanning tools |
| `threshold` | str | `"medium"` | Alert threshold: `low`, `medium`, `high` |
| `fail_fast` | bool | `true` | Whether to block the commit when an issue reaches the threshold |

### `[web_search]` — Web Search

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `false` | Whether enabled; disabled by default |
| `provider` | str | `"duckduckgo"` | Search backend |
| `max_results` | int | `3` | Maximum number of results returned |
| `timeout` | float | `10.0` | Request timeout (seconds) |

!!! warning "Privacy Notice"
    When `web_search` is enabled, error summaries are sent to a public search service. Make sure you are willing to share this information before enabling it.

### `[docker_ship]` — Docker Build & Push

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Whether enabled |
| `default_image` | str | `null` | Default image name |
| `default_tag` | str | `"latest"` | Default tag |
| `push` | bool | `false` | Whether to push after building |
| `build_args` | dict | `{}` | Build arguments |

## Configuration File Search Path

AutoShip looks for the configuration file in the following order:

1. The path specified by `--config`
2. `.autoship.toml` in the current working directory
3. `.autoship.toml` in the project root directory
