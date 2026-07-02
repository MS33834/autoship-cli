---
title: 設定説明
---
# 設定説明

AutoShip は `.autoship.toml` をプロジェクトレベルの設定ファイルとして使用します。`autoship init` の実行時にプロジェクトタイプとハードウェアに基づいてデフォルト設定が自動作成されます。

## 完全な例

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

## 設定項目の説明

### トップレベル

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `schema_version` | int | `1` | 設定ファイルのバージョン |
| `project_type` | str | `"python"` | プロジェクトタイプ。デフォルトテンプレートに影響 |
| `log_level` | str | `"INFO"` | ログレベル |
| `telemetry_enabled` | bool | `false` | テレメトリを有効にするかどうか |
| `audit_log_dir` | path | `null` | 監査ログディレクトリ |

### `[model]` — モデルルーティング

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `default_tier` | 1/2/3 | `2` | デフォルトのモデル階層。数値が大きいほど能力が高い |
| `fallback` | bool | `true` | 優先バックエンドの失敗時にフォールバックするかどうか |
| `backends` | array | `[]` | モデルバックエンドのリスト |

#### `[[model.backends]]`

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `provider` | str | 必須 | バックエンドタイプ：`ollama`、`lm_studio`、`llama_cpp`、`vllm` |
| `base_url` | url | 必須 | バックエンド API アドレス |
| `api_key` | str | `null` | API キー。環境変数からの注入を推奨 |
| `model` | str | `null` | モデル名 |
| `timeout` | float | `30.0` | リクエストタイムアウト（秒） |
| `concurrency` | int | `2` | 並行数 |
| `priority` | int | `0` | 優先度。数値が大きいほど優先される |

### `[clean]` — コードクリーンアップ

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `enabled` | bool | `true` | 有効かどうか |
| `tools` | array | `["autoflake", "black"]` | フォーマットとクリーンアップツール |
| `exclude` | array | `[]` | 除外パス |

### `[commit]` — コミット生成

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `enabled` | bool | `true` | 有効かどうか |
| `max_tokens` | int | `512` | コミットメッセージ生成の最大トークン数 |
| `conventional_commits` | bool | `true` | Conventional Commits スタイルを生成するかどうか |
| `auto_push` | bool | `false` | コミット後に自動プッシュするかどうか |

### `[security]` — セキュリティスキャン

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `enabled` | bool | `true` | 有効かどうか |
| `tools` | array | `["bandit"]` | スキャンツール |
| `threshold` | str | `"medium"` | アラート閾値：`low`、`medium`、`high` |
| `fail_fast` | bool | `true` | 閾値に達する問題を発見した場合にコミットをブロックするかどうか |

### `[web_search]` — Web 検索

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `enabled` | bool | `false` | 有効かどうか。デフォルトは無効 |
| `provider` | str | `"duckduckgo"` | 検索バックエンド |
| `max_results` | int | `3` | 最大結果数 |
| `timeout` | float | `10.0` | リクエストタイムアウト（秒） |

!!! warning "プライバシーに関する注意"
    `web_search` を有効にすると、エラーサマリーが公開検索サービスに送信されます。この情報の共有に同意した場合のみ有効にしてください。

### `[docker_ship]` — Docker ビルドとプッシュ

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `enabled` | bool | `true` | 有効かどうか |
| `default_image` | str | `null` | デフォルトのイメージ名 |
| `default_tag` | str | `"latest"` | デフォルトのタグ |
| `push` | bool | `false` | ビルド後にプッシュするかどうか |
| `build_args` | dict | `{}` | ビルド引数 |

## 設定ファイルの検索パス

AutoShip は以下の順序で設定ファイルを検索します：

1. `--config` で指定されたパス
2. 現在の作業ディレクトリの `.autoship.toml`
3. プロジェクトルートディレクトリの `.autoship.toml`
