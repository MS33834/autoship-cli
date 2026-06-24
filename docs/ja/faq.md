# よくある質問（FAQ）

## 一般的な質問

### AutoShip は私のコードをアップロードしますか？

いいえ。デフォルトでは、すべてのコア処理（クリーンアップ、検証、コミットメッセージ生成）はローカルで完結します。外部モデルバックエンド（OpenAI など）やアップロードターゲット（PyPI、Docker Registry）を明示的に設定した場合のみ、必要なデータが該当サービスに送信されます。詳細は [プライバシーポリシー](privacy.md) を参照してください。

### AutoShip の使用にインターネット接続は必要ですか？

コアコマンド（`init`、`clean`、`commit`、`verify`）は完全にオフライン環境で実行できます。インターネット接続が必要な機能は以下の通りです：

- PyPI / Docker / GitHub への `upload`
- `web-search` プラグインの Web 検索
- PyPI やリモートレジストリからの `plugin install`
- クラウドモデルバックエンドの使用

### AutoShip はどのオペレーティングシステムをサポートしていますか？

AutoShip は Linux、macOS、Windows で実行できます。CI でもこれら 3 つのプラットフォーム向けにバイナリ実行可能ファイルをビルドしています。推奨 Python バージョンは 3.10 以上です。

## インストールとアップグレード

### AutoShip をインストールするには？

推奨される方法：

```bash
pipx install autoship
```

または uv を使用：

```bash
uv tool install autoship
```

開発者はリポジトリをクローン後、`uv sync --all-extras --dev` でインストールできます。

### 最新バージョンにアップグレードするには？

```bash
pipx upgrade autoship
# または
pip install --upgrade autoship
```

### `autoship` コマンドが見つかりません。どうすればよいですか？

1. インストールが成功しているか確認：`pipx list` または `pip show autoship`。
2. PATH に pipx / Python scripts ディレクトリが含まれているか確認。
3. 仮想環境を使用している場合は、環境が有効化されているか確認。

## モデルと AI

### OpenAI / Claude / Azure などのクラウドモデルを使用できますか？

はい。`.autoship.toml` の `[model.backends]` で該当する provider（`openai`、`azure_openai`、`openrouter` など）を設定してください。API キーは環境変数から注入することを推奨し、設定ファイルへの書き込みを避けてください。

```toml
[[model.backends]]
provider = "openai"
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key = "${OPENAI_API_KEY}"
```

### ローカルモデルのおすすめは？

- [Ollama](https://ollama.com/)：入門が最もシンプルで、複数のオープンソースモデルをサポート。
- [LM Studio](https://lmstudio.ai/)：グラフィカルインターフェース付きで、ローカル実験に適する。
- [llama.cpp](https://github.com/ggerganov/llama.cpp) または [vLLM](https://github.com/vllm-project/vllm)：GPU を持つ上級者向け。

詳細は [モデル設定](models.md) を参照。

### モデルバックエンドへの接続に失敗します。どうすればよいですか？

1. `autoship doctor` を実行してモデルバックエンドの状態を確認。
2. バックエンドサービスが起動しており、`base_url` が正しいか確認。
3. ファイアウォールやプロキシ設定を確認。
4. ログを確認：`autoship --verbose <command>`。

## 設定

### 設定ファイルはどこに置きますか？

プロジェクトレベルの設定：`.autoship.toml`（プロジェクトルートディレクトリ）。

チームレベルの設定：`.autoship.team.toml`（プロジェクトルートディレクトリ、プロジェクト設定で上書き可能）。

グローバル設定：

- Linux/macOS：`~/.config/autoship/config.toml`
- Windows：`%APPDATA%\autoship\config.toml`

### テレメトリを無効化するには？

テレメトリはデフォルトで無効です。明示的に確認する場合：

```toml
[telemetry]
enabled = false
```

### 言語を切り替えるには？

```bash
autoship --lang en <command>
# または設定で
locale = "en"
```

## プラグイン

### サードパーティプラグインをインストールするには？

```bash
autoship plugin install my-plugin
```

インストール後のデフォルトの信頼レベルは `community` です。ソースコードをレビュー後に `verified` に昇格できます：

```bash
autoship plugin trust my-plugin verified
```

### 自分のプラグインを開発するには？

[プラグイン開発ガイド](plugin-development.md) とサンプルプラグイン [`examples/custom-plugin`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin) を参照してください。

### プラグインはシステムコマンドを実行できますか？

はい。ただし `permissions` で `shell = true` を宣言し、ユーザーの確認が必要です。最小権限の原則に従うことを推奨します。

## セキュリティと監査

### AutoShip は私の資格情報をどのように保護しますか？

- 監査ログとエラーログはデフォルトで API キー、トークン、パスワードなどの機密情報をマスキングします。
- キーは環境変数から注入することを推奨し、設定ファイルへの書き込みを避けてください。
- 設定ファイルの権限はシステムにより所有者のみ読み書き可能に自動設定されます。

### 監査ログはどのくらい保持されますか？

デフォルトで 30 日間保持します。`.autoship.toml` で設定可能です：

```toml
[audit]
retention_days = 30
```

手動クリーンアップ：

```bash
autoship audit cleanup
```

### セキュリティ脆弱性を発見した場合、どう報告すればよいですか？

公開 issue を作成せず、`security@autoship.dev` までメールで非公開に報告してください。詳細は [セキュリティポリシー](security.md) を参照。

## トラブルシューティング

### `autoship verify` が失敗しますが、テスト自体には問題がありません。

`verify` コマンドは指定されたテスト/チェックコマンドを先に実行し、その後 AutoShip の検証フローを実行します。以下を確認してください：

1. 呼び出されたテストコマンド自体がパスしているか。
2. `pre_verify` / `post_verify` フェーズで失敗しているプラグインがないか。
3. `--verbose` で詳細ログを確認。

### `autoship commit` の生成メッセージが不満です。

`--edit` でエディタを開いて生成されたメッセージを修正するか、設定で `commit.max_tokens` と `conventional_commits` を調整できます。

### AutoShip の設定をリセットするには？

プロジェクトルートディレクトリの `.autoship.toml` を削除し、再度 `autoship init` を実行してください。
