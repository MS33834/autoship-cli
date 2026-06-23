# AutoShip CLI

> ローカル優先のインテリジェントなデリバリーアシスタント

AutoShip-CLI は、開発後のクリーンアップ、検証、コミット、アップロードのワークフローを自動化するツールです。すべてのコア処理はデフォルトでローカルで実行され、コードをクラウドに送信する必要はありません。

## 主な機能

- **ローカル優先**：デフォルトでローカル AI モデルとローカルツールチェーンを使用し、コードの漏洩を防ぎます。
- **プラグイン化**：[pluggy](https://pluggy.readthedocs.io/) ベースの Hook システムで自由に拡張可能。
- **モデル階層**：ハードウェアとタスクに応じて異なるモデル階層に自動ルーティング。
- **安全かつ信頼性が高い**：監査ログ、資格情報の暗号化、プラグインサンドボックス、コミット前のセキュリティスキャン。

## インストール

依存関係を分離するため、[pipx](https://pypa.github.io/pipx/) を使ったインストールを推奨します：

```bash
pipx install autoship
```

または [uv](https://docs.astral.sh/uv/) を使用：

```bash
uv tool install autoship
```

開発者はリポジトリをクローンして uv を直接使用できます：

```bash
git clone https://github.com/MS33834/autoship-cli.git
cd autoship-cli
uv sync --all-extras --dev
```

## クイックスタート

プロジェクトのルートディレクトリで以下を実行してください：

```bash
# AutoShip 設定を初期化
autoship init

# コードをクリーンアップしてフォーマット
autoship clean

# コミットメッセージを生成してコミット
autoship commit

# 検証を実行
autoship verify pytest

# アーティファクトをアップロード（例：Docker）
autoship upload --target docker --image myapp --tag latest
```

## グローバルオプション

すべてのコマンドは以下のグローバルオプションをサポートしています：

| オプション | 説明 |
|---|---|
| `-v, --verbose` | より詳細なログを出力 |
| `-n, --dry-run` | 実際には実行せず、操作をプレビュー |
| `-y, --yes` | 対話式の確認をスキップ |
| `-c, --config PATH` | 設定ファイルのパスを指定 |

## 次のステップ

- 各コマンドの詳細な使い方は [コマンドリファレンス](../commands/index.md) を参照。
- `.autoship.toml` の設定項目は [設定説明](../configuration.md) を参照。
- AutoShip を拡張する方法は [プラグイン](../plugins.md) と [プラグイン開発ガイド](../plugin-development.md) を参照。
