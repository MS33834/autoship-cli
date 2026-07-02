# AutoShip-CLI

<p align="right">
  <a href="README.md">English</a> |
  <a href="README.zh.md">中文</a> |
  <strong>日本語</strong>
</p>

> AutoShip は、ローカル優先のインテリジェントなデリバリー用「清掃担当」です。マシンから離れることなく、プロジェクトのクリーンアップ、検証、コミット、アーティファクトのデリバリーを自動化します。

[![PyPI](https://img.shields.io/pypi/v/autoship)](https://pypi.org/project/autoship/)
[![Python](https://img.shields.io/pypi/pyversions/autoship)](https://pypi.org/project/autoship/)
[![License](https://img.shields.io/github/license/MS33834/autoship-cli)](./LICENSE)
[![CI](https://github.com/MS33834/autoship-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/MS33834/autoship-cli/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-ms33834.github.io%2Fautoship--cli%2Fdocs-blue)](https://ms33834.github.io/autoship-cli/docs)

[テキスト版デモを見る](docs/demo.md)

> デモは近日公開予定、[デモスクリプト](docs/demo.md) をご確認ください。
> asciinema の録画が完了したら、以下のコマンドで生成された `docs/demo.cast` に置き換わります：
>
> ```bash
> asciinema rec docs/demo.cast --command "autoship init && autoship clean && autoship commit"
> ```
>
> 公式サイト：[ms33834.github.io/autoship-cli](https://ms33834.github.io/autoship-cli/)

## ロードマップ

> **提供済み**：P1–P3 + P4-1（セキュリティ強化、プラグインストア、実 AI/アップロード統合、CI パイプライン、テレメトリプライバシー、自動 Changelog）。完全な回査監査完了：670 テスト合格、カバレッジ 87.88%、ruff + pyright + bandit 全クリーン。提供済み機能の概要は [`FEATURES.md`](./FEATURES.md) を参照。
>
> **次のステップ**：P4-2 → P4-6（公開ドキュメントサイト、コミュニティプラグイン、パフォーマンス/スケール、セキュリティ監査、ローンチ）および P5 の前方拡張。チェックボックス付きのライブロードマップ（更新のたびに両リモートへ同期）は [`PLAN.md`](./PLAN.md) にあります。

## インストール

### 推奨：pipx

```bash
pipx install autoship
```

### pip を使用する場合

```bash
pip install autoship
```

### ソースからインストール

```bash
git clone https://github.com/MS33834/autoship-cli.git
cd autoship-cli
uv sync --all-extras --dev
uv run autoship --help
```

### バイナリダウンロード

各プラットフォーム向けのプリコンパイル済みバイナリは GitHub Releases から入手できます：

- [最新版をダウンロード](https://github.com/MS33834/autoship-cli/releases/latest)

> バイナリは CI によって自動公開されます。

## クイックスタート

```bash
# プロジェクト設定を初期化
autoship init

# コードをクリーンアップしてフォーマット
autoship clean

# コミットメッセージを生成してコミット
autoship commit

# 検証を実行（pytest の例）
autoship verify pytest

# アーティファクトをアップロード（例：Docker イメージ）
autoship upload --target docker --image myapp --tag latest
```

## 主な機能

- **ローカル優先**：デフォルトでローカル AI モデルとローカルツールチェーンを使用し、コードを外部に送信しません。
- **プラグイン化**：清理・検証・アップロードなどのフェーズを拡張できる [pluggy](https://pluggy.readthedocs.io/) ベースの Hook システム。
- **プラグイン開発 SDK**：[`autoship-sdk`](https://pypi.org/project/autoship-sdk/) が基底クラス、Hook デコレーター、テスト用足場を提供します。
- **モデル階層**：ハードウェア構成とタスク種別に応じて異なる階層のモデルに自動ルーティングし、速度と品質を両立。
- **セキュリティスキャン**：コミット前に依存関係の脆弱性とコードセキュリティスキャンを実行し、リスクをブロック。
- **監査ログ**：コマンド実行、モデル呼び出し、設定変更を完全に記録し、構造化されたエクスポートと自動クリーンアップをサポート。
- **環境診断**：`autoship doctor` で Python、Git、モデルバックエンド、ツールチェーン、ディレクトリ権限をワンクリックでチェック。
- **多言語 CLI**：`--lang zh|en|ja` または `locale` 設定で、中国語・英語・日本語を切り替え可能。
- **Telemetry はデフォルトで無効**：匿名利用データは、明示的にオプトインしない限り送信されません。

## ドキュメント

- 完全なドキュメント：[ms33834.github.io/autoship-cli/docs](https://ms33834.github.io/autoship-cli/docs)
- ローカルドキュメント：[docs/](./docs/)
- コマンドリファレンス：[docs/commands/index.md](./docs/commands/index.md)
- 設定説明：[docs/configuration.md](./docs/configuration.md)
- プラグイン開発ガイド：[docs/plugin-development.md](./docs/plugin-development.md)

## よくある質問

### AutoShip は私のコードをアップロードしますか？

いいえ。すべてのコア処理はデフォルトでローカルで実行されます。外部モデルやアップロード先（Docker Registry、PyPI など）を明示的に設定した場合のみ、それらのサービスに必要なデータが送信されます。

### AutoShip はインターネット接続を必要としますか？

コアコマンド（`init`、`clean`、`commit`、`verify`）はオフラインで実行できます。`upload` や Web 検索/外部モデルに依存する機能のみ、インターネット接続が必要です。

### Telemetry を無効にするには？

Telemetry はデフォルトで無効なので、追加の操作は不要です。有効にするには `.autoship.toml` で `telemetry.enabled = true` を設定してください。

Telemetry のフィールドとエンドポイントのセキュリティルールについては [docs/telemetry.md](./docs/telemetry.md) を、完全なプライバシーポリシーとユーザーの権利については [docs/privacy.md](./docs/privacy.md) を参照してください。

### カスタムプラグインを開発するには？

[docs/plugin-development.md](./docs/plugin-development.md) とサンプルプラグイン [examples/custom-plugin/](./examples/custom-plugin/) を参照してください。

### AutoShip は商用プロジェクトで使用できますか？

はい。本プロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](./LICENSE) を参照してください。

## 貢献とセキュリティ

- 貢献ガイド：[CONTRIBUTING.md](./CONTRIBUTING.md)
- セキュリティ報告：[SECURITY.md](./SECURITY.md)

## ライセンス

MIT
