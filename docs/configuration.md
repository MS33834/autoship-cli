# 配置说明

AutoShip 使用 `.autoship.toml` 作为项目级配置文件。运行 `autoship init` 时会根据项目类型与硬件自动创建默认配置。

## 完整示例

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

## 配置项说明

### 顶层

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `schema_version` | int | `1` | 配置文件版本 |
| `project_type` | str | `"python"` | 项目类型，影响默认模板 |
| `log_level` | str | `"INFO"` | 日志级别 |
| `telemetry_enabled` | bool | `false` | 是否启用遥测 |
| `audit_log_dir` | path | `null` | 审计日志目录 |

### `[model]` — 模型路由

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `default_tier` | 1/2/3 | `2` | 默认模型层级，数字越大能力越强 |
| `fallback` | bool | `true` | 首选后端失败时是否降级 |
| `backends` | array | `[]` | 模型后端列表 |

#### `[[model.backends]]`

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `provider` | str | 必填 | 后端类型：`ollama`、`lm_studio`、`llama_cpp`、`vllm` |
| `base_url` | url | 必填 | 后端 API 地址 |
| `api_key` | str | `null` | API 密钥，建议通过环境变量注入 |
| `model` | str | `null` | 模型名称 |
| `timeout` | float | `30.0` | 请求超时（秒） |
| `concurrency` | int | `2` | 并发数 |
| `priority` | int | `0` | 优先级，数值越大越优先 |

### `[clean]` — 代码清理

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enabled` | bool | `true` | 是否启用 |
| `tools` | array | `["autoflake", "black"]` | 格式化和清理工具 |
| `exclude` | array | `[]` | 排除路径 |

### `[commit]` — 提交生成

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enabled` | bool | `true` | 是否启用 |
| `max_tokens` | int | `512` | 生成提交信息的最大 token 数 |
| `conventional_commits` | bool | `true` | 是否生成 Conventional Commits 风格 |
| `auto_push` | bool | `false` | 提交后是否自动推送 |

### `[security]` — 安全扫描

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enabled` | bool | `true` | 是否启用 |
| `tools` | array | `["bandit"]` | 扫描工具 |
| `threshold` | str | `"medium"` | 告警阈值：`low`、`medium`、`high` |
| `fail_fast` | bool | `true` | 发现达到阈值的问题时是否阻止提交 |

### `[web_search]` — 联网搜索

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enabled` | bool | `false` | 是否启用，默认关闭 |
| `provider` | str | `"duckduckgo"` | 搜索后端 |
| `max_results` | int | `3` | 最大返回结果数 |
| `timeout` | float | `10.0` | 请求超时（秒） |

!!! warning "隐私提醒"
    启用 `web_search` 后，错误摘要会被发送到公共搜索服务。请确认你愿意共享这些信息。

### `[docker_ship]` — Docker 构建与推送

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enabled` | bool | `true` | 是否启用 |
| `default_image` | str | `null` | 默认镜像名称 |
| `default_tag` | str | `"latest"` | 默认标签 |
| `push` | bool | `false` | 构建后是否推送 |
| `build_args` | dict | `{}` | 构建参数 |

## 配置文件搜索路径

AutoShip 会按以下顺序查找配置文件：

1. `--config` 指定的路径
2. 当前工作目录下的 `.autoship.toml`
3. 项目根目录下的 `.autoship.toml`
