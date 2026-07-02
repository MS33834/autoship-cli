---
title: audit
---
# audit

監査ログをエクスポートまたはクリーンアップします。監査ログはデフォルトでプロジェクトルートディレクトリの `.autoship/audit/` に保存され、設定や環境変数で調整できます。

## 構文

```bash
autoship audit [OPTIONS] COMMAND [ARGS]...
```

## 引数

`audit` コマンド自体は位置引数を受け取りません。サブコマンドで操作します。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | ヘルプ情報を表示して終了 |

## サブコマンド

### audit export

監査レコードを JSON Lines ファイルにエクスポートします。

```bash
autoship audit export [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| `-s` | `--since TEXT` | - | 指定日時以降のレコードのみエクスポート（ISO 日付または `1d`/`7d`/`30d`） |
| `-o` | `--output PATH` | - | 出力ファイルのパス |

### audit cleanup

保持期間を超えた監査ログファイルを削除します。

```bash
autoship audit cleanup [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--retention-days INTEGER` | - | 保持日数 |
| - | `--dry-run` | `False` | 操作のプレビューのみ |

## 例

直近 30 日間の監査レコードをエクスポート：

```bash
autoship audit export --since 30d
```

指定ファイルにエクスポート：

```bash
autoship audit export --since 2025-01-01 --output ./audit.jsonl
```

90 日以前のログをクリーンアップ：

```bash
autoship audit cleanup --retention-days 90
```

削除対象のログをプレビュー：

```bash
autoship audit cleanup --retention-days 90 --dry-run
```

## 出力の注意点 / よくあるエラー

- `--since` は ISO 日付（例：`2025-01-01`）または相対日数（例：`1d`、`7d`、`30d`）をサポートします。
- `--output` 未指定時は通常デフォルトパス（例：`./audit.jsonl`）に書き込まれます。具体的な動作は実装に依存します。
- クリーンアップ操作は取り消せません。先に `--dry-run` でプレビューすることを推奨します。

## 関連コマンド

- [config](./config.md) — 監査ディレクトリなどの設定を確認・変更
- [doctor](./doctor.md) — 監査ディレクトリの権限をチェック
