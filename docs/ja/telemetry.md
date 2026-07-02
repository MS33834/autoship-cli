---
title: テレメトリとプライバシー
---
# テレメトリとプライバシー（Telemetry & Privacy）

AutoShip はデフォルトで**テレメトリを無効化**しています。明示的に有効化した場合のみ、匿名の使用統計情報を収集して送信します。

## 収集するデータ

テレメトリ有効時、各コマンド終了時に以下のフィールドがアップロードされます：

| フィールド | 例 | 説明 |
|---|---|---|
| `command` | `"clean"` | コマンド名 |
| `exit_code` | `0` | 終了コード |
| `duration_ms` | `123.45` | コマンド実行時間（ミリ秒） |
| `exception_type` | `"ConfigError"` | 例外タイプ（該当時） |
| `exception_lineno` | `42` | 例外発生行番号（該当時） |
| `python_version` | `"3.12.4"` | Python メジャーバージョン |
| `platform` | `"Linux"` | オペレーティングシステムファミリ |
| `metrics_summary` | `{...}` | グローバルカウンターのサマリー |

**以下の内容は一切収集されません：**

- ファイル内容、diff、ソースコード
- ファイルパス、作業ディレクトリ、ホスト名
- コマンド引数、環境変数
- API キー、トークン、パスワード、メールなどの資格情報
- ユーザー名またはその他の個人識別情報（PII）

ローカルログまたはリモート送信されるすべてのレコードは、事前に PII フィルターを通過し、パス、キー、メールなどの機密値は `<path>` や `<redacted>` に置換されます。

## 有効化・無効化の方法

### コマンドライン

```bash
# テレメトリを有効化
autoship config telemetry --enable

# テレメトリを無効化
autoship config telemetry --disable

# 現在の状態を確認
autoship config telemetry --status
```

### 設定ファイル

`.autoship.toml` に追加：

```toml
[telemetry]
enabled = true
endpoint = "https://telemetry.autoship.dev/v1/events"
batch_size = 10
timeout = 5.0
allow_untrusted_endpoint = false
```

旧版設定の `telemetry_enabled = false` も引き続き互換性があり、起動時に自動的に `[telemetry].enabled` に移行されます。

## リモートエンドポイントのセキュリティルール

- `https://` エンドポイントのみ受け付け。
- デフォルトでは `telemetry.autoship.dev` への送信のみ許可。
- 他のドメインへ送信するには以下を同時に満たす必要があります：
  - 設定ファイルで `allow_untrusted_endpoint = true` を設定。
  - または環境変数 `AUTOSHIP_TELEMETRY_ALLOW_UNTRUSTED=1` を設定。
- リクエストタイムアウトはデフォルト 5 秒、最大 30 秒まで。

## バッチ送信とローカルログ

テレメトリイベントはまずローカルの `~/.autoship/telemetry.logl` に書き込まれ、メモリでバッファリングされます。バッファ数が `batch_size`（デフォルト 10）に達するか、CLI 終了前に `flush()` が呼び出された時点で、設定されたエンドポイントに一括送信されます。送信失敗は CLI の通常使用に影響しません。

## プライバシーポリシーサマリー

1. デフォルトは無効で、ユーザーが完全に制御。
2. データは匿名化され、PII を含まない。
3. すべての送信テレメトリは HTTPS を使用し、ドメイン検証で保護。
4. ローカルログとリモートデータはマスキング処理済み。
5. ユーザーはいつでも `autoship config telemetry --disable` で脱退可能。

ローカルのテレメトリ内容を監査する場合は、`~/.autoship/telemetry.logl`（JSON Lines 形式）を確認できます。
