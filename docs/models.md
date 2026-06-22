# 模型配置与后端

AutoShip 的 AI 功能（如生成 commit message、错误修复建议）通过**模型路由层**统一调度。你可以在 `.autoship.toml` 中配置多个后端，系统会根据模型层级、优先级与可用性自动选择。

## 模型层级

| 层级 | 定位 | 典型场景 |
|---|---|---|
| Tier 1 | 轻量快速 | 笔记本 CPU、简单提交信息生成 |
| Tier 2 | 均衡 | 日常开发、常规错误修复 |
| Tier 3 | 能力最强 | 复杂推理、企业级硬件/GPU |

`autoship init` 会根据硬件信息给出默认 tier 建议，也可手动配置：

```toml
[model]
default_tier = 2
fallback = true
```

## 支持的后端

### Ollama

[Ollama](https://ollama.com/) 是最简单的本地模型运行方式。

```toml
[[model.backends]]
provider = "ollama"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen2.5:7b"
timeout = 30.0
concurrency = 2
priority = 0
```

1. 安装并启动 Ollama：`ollama serve`
2. 拉取模型：`ollama pull qwen2.5:7b`
3. 运行 `autoship doctor` 确认后端可达。

### LM Studio

[LM Studio](https://lmstudio.ai/) 提供图形界面与本地 OpenAI-compatible 服务。

```toml
[[model.backends]]
provider = "lm_studio"
base_url = "http://127.0.0.1:1234/v1"
model = "qwen2.5-7b-instruct"
timeout = 30.0
concurrency = 1
priority = 1
```

在 LM Studio 中启动本地服务器，并确保勾选「OpenAI-compatible API」。

### OpenAI / OpenAI-compatible

适用于 OpenAI 官方 API 或任何兼容服务。

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

适用于通过 llama.cpp 启动的本地 HTTP 服务。

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

适用于高并发本地/私有部署。

```toml
[[model.backends]]
provider = "vllm"
base_url = "http://127.0.0.1:8000/v1"
model = "Qwen/Qwen2.5-7B-Instruct"
timeout = 60.0
concurrency = 8
priority = 2
```

## 配置字段说明

| 字段 | 必填 | 说明 |
|---|---|---|
| `provider` | 是 | 后端类型 |
| `base_url` | 是 | API 基础地址 |
| `model` | 是 | 模型名称或部署名 |
| `api_key` | 视 provider | 密钥，建议用 `${ENV_VAR}` 形式引用环境变量 |
| `timeout` | 否 | 单次请求超时（秒），默认 `30.0` |
| `concurrency` | 否 | 该后端最大并发数，默认 `2` |
| `priority` | 否 | 优先级，数值越大越优先，默认 `0` |
| `tier` | 否 | 该后端所属的模型层级，默认由 `model` 推断 |

## 密钥管理最佳实践

**不要**将真实 API key 写入 `.autoship.toml`。推荐做法：

```toml
api_key = "${OPENAI_API_KEY}"
```

并在 shell 中设置：

```bash
export OPENAI_API_KEY="sk-..."
```

AutoShip 会在加载配置时自动解析环境变量，并在日志中脱敏显示。

## 多后端与降级

当 `model.fallback = true` 时，如果首选后端失败（超时、不可用、返回错误），AutoShip 会按优先级尝试下一个同 tier 后端。你可以同时配置本地模型与云端模型，实现「本地优先、云端兜底」。

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

## 隐私与安全

- 本地后端（Ollama、LM Studio、llama.cpp、vLLM）不会将代码发送到外部服务。
- 使用云端后端时，AutoShip 仅发送必要的上下文（如 diff、错误摘要），不会上传整个代码库。
- 所有后端通信默认启用 HTTPS 证书校验；自定义或内部 CA 可在配置中开启 `allow_untrusted_endpoint`（不推荐用于生产）。

## 故障排查

运行 `autoship doctor` 可快速检查：

- 配置文件中声明的后端是否可达
- 环境变量中的 API key 是否存在
- 网络连通性与超时设置是否合理

如需查看模型调用详细日志：

```bash
autoship --verbose commit
```
