# init

現在のプロジェクトに AutoShip 設定ファイルを初期化し、`.autoship.toml` を自動生成してプロジェクトタイプとハードウェア能力を検出します。

## 構文

```bash
autoship init [OPTIONS]
```

## 引数

`init` コマンドは位置引数を受け取りません。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--type TEXT` | - | プロジェクトタイプを強制指定 |
| `-o` | `--output PATH` | `.autoship.toml` | 設定ファイルの出力パス |
| `-y` | `--yes` | `False` | 対話式の確認をスキップ |

## 例

現在のディレクトリにデフォルト設定を生成：

```bash
autoship init
```

出力例：

```text
Created .autoship.toml
```

プロジェクトタイプを強制指定：

```bash
autoship init --type python
```

出力ファイル名を指定：

```bash
autoship init -o autoship.toml
```

## 出力の注意点 / よくあるエラー

- 現在のディレクトリに既に `.autoship.toml` が存在する場合、`--yes` を使うと確認なしで上書きできます。それ以外の場合は確認プロンプトが表示されます。
- 実行失敗時はディレクトリの書き込み権限を確認してください。

## 関連コマンド

- [clean](./clean.md) — コードをクリーンアップしてフォーマット
- [doctor](./doctor.md) — 環境が実行要件を満たしているか診断
- [config](./config.md) — 設定の確認と管理
