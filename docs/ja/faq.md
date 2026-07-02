---
title: よくある質問（FAQ）
---
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

## クイックスタート関連

### クイックスタートの `verify --fix` が「no AI backend configured」と報告されるのはなぜ？

`verify --fix` には修正提案を生成するための AI モデルが必須です。クイックスタートの「5 分で試す AI なし版」ではモデルバックエンドを未設定のため、`verify --fix` を呼ぶと「no AI backend configured」となります。

- 検証のみでよい場合：`autoship verify pytest`（`--fix` なし）を使用；
- 修正フローを試す場合：[クイックスタート](quickstart.md) の「+5 分で試す AI あり版」に従い Ollama を設定。
- これは仕様でありバグではありません。詳しくは [既知の問題](known-issues.md) を参照。

### クイックスタート完了後、完全な AI 機能を試すにはどう設定すればよい？

1. [Ollama](https://ollama.com/) をインストールして起動；
2. モデルを取得：`ollama pull qwen2.5-coder:1.5b`（より大きなモデルでも可）；
3. `.autoship.toml` の `[model]` セクションで `backend = "ollama"` を設定；
4. `autoship doctor` でバックエンド到達性を確認；
5. `autoship verify --fix pytest` と `autoship commit`（AI 生成メッセージ）を試す。

クラウドモデルを含む全オプションは [モデル設定](models.md) を参照。

### モデルはどう選べばよい？

シーン別に選択：

- **入門 / 低スペック機**：ローカル Ollama + `qwen2.5-coder:1.5b` または `phi3:mini`。高速で VRAM 使用量が低い。
- **高品質ローカル**：`qwen2.5-coder:7b`、`deepseek-coder:6.7b`。VRAM 8GB+ 必要。
- **高品質クラウド**：OpenAI `gpt-4o-mini` / `gpt-4o`、Anthropic Claude、Azure OpenAI。ネットワークと API キーが必要。
- **プライバシー優先**：常にローカルモデルを使用し、クラウド provider は設定しない。

選定表は [モデル設定](models.md) を参照。

### プラグインインストール失敗のトラブルシューティング

`autoship plugin install <name>` が失敗する場合、以下の順で確認：

1. ネットワーク：PyPI に到達可能か？`pip install <name>` は成功するか？
2. 信頼レベル：未レビューのプラグインは確認プロンプトで許可するか、明示的に `autoship plugin trust <name> community` を実行；
3. 権限：プラグインが `shell = true` を宣言する場合、対話確認で許可が必要；
4. 互換性：プラグインが宣言する AutoShip バージョン範囲が現バージョン（`autoship --version`）をカバーするか；
5. ログ：`autoship --verbose plugin install <name>` で詳細エラーを確認。

詳しくは [トラブルシューティング](troubleshooting.md) を参照。

### 三言語ドキュメントの同期戦略

- **ソース言語**：中国語（zh）がソースで、en/ja は翻訳；
- **同期ウィンドウ**：新内容は先に zh に反映され、en/ja は通常数時間〜数日で追従；
- **CI 検証**：i18n 完全性チェックが三言語のファイル一覧を比較し、ページや項目の欠落を警告；
- **コマンドコードブロックは翻訳しない**：shell / toml / yaml コードブロックは三言語すべてで英語のまま、コメントと本文のみローカライズ；
- **リンクの相対パス**：ページ間リンクは相対パスを使用し、三言語のディレクトリ構造は一致（`docs/`、`docs/en/`、`docs/ja/`）。

翻訳の遅れや欠落に気付いた場合は [GitHub Issues](https://github.com/MS33834/autoship-cli/issues) で報告してください。
