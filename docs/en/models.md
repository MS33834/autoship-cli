---
title: Model Configuration & Backends
---
# Model Configuration & Backends

AutoShip's AI features (such as generating commit messages and error-fix suggestions) are dispatched uniformly through the **model routing layer**. You can configure multiple backends in `.autoship.toml`, and the system will automatically select one based on model tier, priority, and availability.

## Model Tiers

| Tier | Positioning | Typical Scenarios |
|---|---|---|
| Tier 1 | Lightweight & fast | Laptop CPUs, simple commit message generation |
| Tier 2 | Balanced | Daily development, routine error fixes |
| Tier 3 | Most capable | Complex reasoning, enterprise-grade hardware/GPU |

`autoship init` provides a default tier recommendation based on hardware information, but it can also be configured manually:

```toml
[model]
default_tier = 2
fallback = true
```

## Supported Backends

### Ollama

[Ollama](https://ollama.com/) is the simplest way to run local models.

```toml
[[model.backends]]
provider = "ollama"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen2.5:7b"
timeout = 30.0
concurrency = 2
priority = 0
```

1. Install and start Ollama: `ollama serve`
2. Pull the model: `ollama pull qwen2.5:7b`
3. Run `autoship doctor` to confirm the backend is reachable.

### LM Studio

[LM Studio](https://lmstudio.ai/) provides a graphical interface and a local OpenAI-compatible service.

```toml
[[model.backends]]
provider = "lm_studio"
base_url = "http://127.0.0.1:1234/v1"
model = "qwen2.5-7b-instruct"
timeout = 30.0
concurrency = 1
priority = 1
```

Start the local server in LM Studio and make sure "OpenAI-compatible API" is checked.

### OpenAI / OpenAI-compatible

Applicable to the official OpenAI API or any compatible service.

```toml
[[model.backends]]
provider = "openai"
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key = "${OPENAI_API_KEY}"
timeout = 60.0
concurrency = 4
priority = 2
```

### Azure OpenAI

```toml
[[model.backends]]
provider = "azure_openai"
base_url = "https://<your-resource>.openai.azure.com/openai/deployments/<deployment>"
model = "gpt-4o"
api_key = "${AZURE_OPENAI_API_KEY}"
timeout = 60.0
concurrency = 4
priority = 2
```

### OpenRouter

```toml
[[model.backends]]
provider = "openrouter"
base_url = "https://openrouter.ai/api/v1"
model = "anthropic/claude-3.5-sonnet"
api_key = "${OPENROUTER_API_KEY}"
timeout = 60.0
concurrency = 2
priority = 1
```

### llama.cpp

Applicable to local HTTP services started via llama.cpp.

```toml
[[model.backends]]
provider = "llama_cpp"
base_url = "http://127.0.0.1:8080/v1"
model = "local-model"
timeout = 60.0
concurrency = 1
priority = 0
```

### vLLM

Applicable to high-concurrency local/private deployments.

```toml
[[model.backends]]
provider = "vllm"
base_url = "http://127.0.0.1:8000/v1"
model = "Qwen/Qwen2.5-7B-Instruct"
timeout = 60.0
concurrency = 8
priority = 2
```

## Configuration Field Reference

| Field | Required | Description |
|---|---|---|
| `provider` | Yes | Backend type |
| `base_url` | Yes | API base URL |
| `model` | Yes | Model name or deployment name |
| `api_key` | Depends on provider | Key; referencing environment variables via `${ENV_VAR}` is recommended |
| `timeout` | No | Single request timeout (seconds), default `30.0` |
| `concurrency` | No | Maximum concurrency for this backend, default `2` |
| `priority` | No | Priority; higher values are preferred, default `0` |
| `tier` | No | Model tier this backend belongs to; inferred from `model` by default |

## Key Management Best Practices

**Do not** write real API keys into `.autoship.toml`. The recommended approach:

```toml
api_key = "${OPENAI_API_KEY}"
```

And set it in your shell:

```bash
export OPENAI_API_KEY="sk-..."
```

AutoShip automatically resolves environment variables when loading the configuration and masks them in logs.

## Multiple Backends & Fallback

When `model.fallback = true`, if the preferred backend fails (timeout, unavailable, returns an error), AutoShip will try the next backend of the same tier by priority. You can configure both local and cloud models at the same time to achieve "local first, cloud fallback".

```toml
[model]
default_tier = 2
fallback = true

[[model.backends]]
provider = "ollama"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen2.5:7b"
priority = 2

[[model.backends]]
provider = "openai"
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key = "${OPENAI_API_KEY}"
priority = 1
```

## Privacy & Security

- Local backends (Ollama, LM Studio, llama.cpp, vLLM) do not send code to external services.
- When using cloud backends, AutoShip only sends the necessary context (such as diffs and error summaries) and never uploads the entire codebase.
- HTTPS certificate verification is enabled by default for all backend communication; custom or internal CAs can use `allow_untrusted_endpoint` in the configuration (not recommended for production).

## Troubleshooting

Run `autoship doctor` to quickly check:

- Whether the backends declared in the configuration file are reachable
- Whether the API keys in environment variables are present
- Whether network connectivity and timeout settings are reasonable

To view detailed model call logs:

```bash
autoship --verbose commit
```
