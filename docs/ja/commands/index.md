# コマンドリファレンス

AutoShip CLI のすべてのコマンドは統一されたライフサイクルに従います：設定の読み込み、`pre_*` Hook の呼び出し、本体の実行、`post_*` Hook の呼び出し、監査ログの記録。本文書は各コマンドの完全な構文、引数、オプション、例を提供します。

## グローバルオプション

以下のオプションはすべてのコマンドに適用され、通常はサブコマンドの前に配置します（例：`autoship --verbose init`）：

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| `-v` | `--verbose` | `False` | より詳細なログを出力 |
| `-n` | `--dry-run` | `False` | 実際には実行せず、操作をプレビュー |
| `-y` | `--yes` | `False` | 対話式の確認をスキップ |
| `-c` | `--config PATH` | - | 設定ファイルのパスを指定 |
| - | `--lang TEXT` | `auto` | 出力言語（`en`、`zh`、`ja`、`auto`） |
| - | `--install-completion` | - | 現在のシェルに自動補完をインストール |
| - | `--show-completion` | - | 現在のシェルの自動補完スクリプトを表示 |

グローバルオプションは `autoship --help` でいつでも確認できます：

```bash
autoship --help
autoship --lang zh --help
```

## コマンド一覧

| コマンド | 説明 | サブコマンド |
|---|---|---|
| [init](./init.md) | 現在のプロジェクトに AutoShip 設定ファイルを初期化 | - |
| [clean](./clean.md) | プロジェクトコードをクリーンアップしてフォーマット | - |
| [verify](./verify.md) | 検証コマンドを実行し、AI 支援による修正のためにエラーをキャプチャ | - |
| [fix](./fix.md) | LLM に直近の検証失敗に対する修正提案を生成させる | - |
| [commit](./commit.md) | コミットメッセージを生成して Git コミットを実行 | - |
| [upload](./upload.md) | 設定されたターゲットにアーティファクトをアップロード | - |
| [plugin](./plugin.md) | プラグインを管理 | `list`、`search`、`info`、`install`、`uninstall`、`rate`、`stats`、`trust`、`update` |
| [doctor](./doctor.md) | AutoShip 環境と依存関係を診断 | - |
| [audit](./audit.md) | 監査ログをエクスポートまたはクリーンアップ | `export`、`cleanup` |
| [registry](./registry.md) | プラグインレジストリの参照とインデックスの同期 | `list`、`dashboard`、`sync` |
| [metrics](./metrics.md) | 実行時メトリクスを確認 | `show`、`export` |
| [config](./config.md) | AutoShip 設定の確認と管理 | `list`、`get`、`telemetry` |

## ドキュメント構成

- `index.md`（このページ）：グローバルオプションとコマンドインデックス。
- `<command>.md`：各コマンドの独立リファレンスページ。概要、構文、引数、オプション、例、出力の注意点、関連コマンドを含みます。
- 複雑なコマンド（`plugin`、`audit`、`registry`、`metrics`、`config`）のリファレンスページにはサブコマンドの詳細説明が含まれます。

## 貢献方法

コマンドリファレンスは CLI の実際の `--help` 出力と一致させてください。編集前に以下を実行してください：

```bash
uv run python -m autoship <cmd> --help
```

新しいコマンドを追加する場合は、このページのコマンド一覧テーブルと `mkdocs.yml` のナビゲーションを同時に更新してください。
