---
title: モデル設定とバックエンド
---
# モデル設定とバックエンド

AutoShip の AI 機能（コミットメッセージの生成、エラー修正提案など）は**モデルルーティングレイヤー**を通じて統一的にスケジュールされます。`.autoship.toml` で複数のバックエンドを設定でき、システムはモデル階層、優先度、可用性に基づいて自動的に選択します。

## モデル階層

| 階層 | 位置づけ | 典型的なシナリオ |
|---|---|---|
| Tier 1 | 軽量・高速 | ノート PC の CPU、シンプルなコミットメッセージ生成 |
| Tier 2 | バランス | 日常的な開発、一般的なエラー修正 |
| Tier 3 | 最高能力 | 複雑な推論、エンタープライズ級ハードウェア/GPU |

`autoship init` はハードウェア情報に基づいてデフォルトの tier 推奨を提示しますが、手動で設定することもできます：

```toml
[model]
default_tier = 2
fallback = true
```

## サポートされているバックエンド

### Ollama

[Ollama](https://ollama.com/) は最もシンプルなローカルモデルの実行方法です。

```toml
[[model.backends]]
provider = "ollama"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen2.5:7b"
timeout = 30.0
concurrency = 2
priority = 0
```

1. Ollama をインストールして起動：`ollama serve`
2. モデルをプル：`ollama pull qwen2.5:7b`
3. `autoship doctor` を実行してバックエンドの到達性を確認。

### LM Studio

[LM Studio](https://lmstudio.ai/) はグラフィカルインターフェースとローカルの OpenAI 互換サービスを提供します。

```toml
[[model.backends]]
provider = "lm_studio"
base_url = "http://127.0.0.1:1234/v1"
model = "qwen2.5-7b-instruct"
timeout = 30.0
concurrency = 1
priority = 1
```

LM Studio でローカルサーバーを起動し、「OpenAI-compatible API」にチェックを入れてください。

### OpenAI / OpenAI 互換

OpenAI 公式 API または互換サービスに適用されます。

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

llama.cpp で起動したローカル HTTP サービスに適用されます。

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

高並行のローカル/プライベートデプロイに適用されます。

```toml
[[model.backends]]
provider = "vllm"
base_url = "http://127.0.0.1:8000/v1"
model = "Qwen/Qwen2.5-7B-Instruct"
timeout = 60.0
concurrency = 8
priority = 2
```

## 設定フィールドの説明

| フィールド | 必須 | 説明 |
|---|---|---|
| `provider` | はい | バックエンドタイプ |
| `base_url` | はい | API ベースアドレス |
| `model` | はい | モデル名またはデプロイ名 |
| `api_key` | provider による | キー。`${ENV_VAR}` 形式で環境変数を参照することを推奨 |
| `timeout` | いいえ | 単一リクエストのタイムアウト（秒）。デフォルト `30.0` |
| `concurrency` | いいえ | このバックエンドの最大並行数。デフォルト `2` |
| `priority` | いいえ | 優先度。数値が大きいほど優先される。デフォルト `0` |
| `tier` | いいえ | このバックエンドが属するモデル階層。デフォルトは `model` から推論 |

## キー管理のベストプラクティス

実際の API キーを `.autoship.toml` に書き込まないでください。推奨される方法：

```toml
api_key = "${OPENAI_API_KEY}"
```

シェルで以下を設定します：

```bash
export OPENAI_API_KEY="sk-..."
```

AutoShip は設定の読み込み時に環境変数を自動的に解決し、ログではマスキングして表示します。

## マルチバックエンドとフォールバック

`model.fallback = true` の場合、優先バックエンドが失敗（タイムアウト、利用不可、エラー返却）すると、AutoShip は優先度順に同じ tier の次のバックエンドを試します。ローカルモデルとクラウドモデルを同時に設定し、「ローカル優先、クラウドフォールバック」を実現できます。

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

## プライバシーとセキュリティ

- ローカルバックエンド（Ollama、LM Studio、llama.cpp、vLLM）はコードを外部サービスに送信しません。
- クラウドバックエンド使用時、AutoShip は必要なコンテキスト（diff、エラーサマリーなど）のみを送信し、コードベース全体をアップロードしません。
- すべてのバックエンド通信はデフォルトで HTTPS 証明書検証が有効です。カスタムまたは内部 CA は設定で `allow_untrusted_endpoint` を有効にできます（本番環境では推奨されません）。

## トラブルシューティング

`autoship doctor` を実行すると以下を素早く確認できます：

- 設定ファイルで宣言されたバックエンドが到達可能か
- 環境変数の API キーが存在するか
- ネットワーク接続性とタイムアウト設定が適切か

モデル呼び出しの詳細ログを確認する場合：

```bash
autoship --verbose commit
```
