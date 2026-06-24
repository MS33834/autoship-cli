# プライバシーポリシー（Privacy Policy）

AutoShip は**ローカル優先**と**デフォルト無効**の原則を堅持しています：明示的に有効にしない限り、使用データの収集、アップロード、共有は行いません。

## 1. 収集するデータ

### 1.1 テレメトリデータ（デフォルト無効）

ユーザーが設定で `[telemetry].enabled = true` を有効にすると、AutoShip は各コマンド終了時に匿名の使用統計をアップロードします。フィールドは以下の通りです：

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

すべてのテレメトリレコードはローカルログへの書き込みまたはリモート送信前に PII フィルターを通過し、パス、キー、メールなどの機密値は `<path>` や `<redacted>` に置換されます。

より詳細なテレメトリ設定、バッチ送信、エンドポイントセキュリティルールについては [docs/telemetry.md](telemetry.md) を参照してください。

### 1.2 監査ログ（ローカルデフォルト有効）

AutoShip はデフォルトでローカルに構造化監査ログを書き込み、セキュリティ調査とコンプライアンス監査に使用します。監査ログには以下が含まれます：

- コマンド呼び出しイベントと終了ステータス
- 設定変更とプラグイン操作
- モデル呼び出しリクエスト（マスキング済み）
- SIEM 転送レコード（有効時）

監査ログもマスキング処理され、機密のキーと値、一般的なトークンパターンは `***` に置換されます。

## 2. データの保存場所

| データタイプ | デフォルトパス | 権限 |
|---|---|---|
| テレメトリローカルログ | `~/.autoship/telemetry.logl` | 所有者読み書き可能 |
| 監査ログ | `~/.autoship/logs/audit.{YYYY-MM-DD}.jsonl` | ディレクトリ `0o700`、ファイル `0o600` |
| 設定とキャッシュ | `~/.autoship/` またはプロジェクトルートディレクトリ | 最小権限の原則に従う |

## 3. データの保持とクリーンアップ

### 3.1 テレメトリローカルログ

テレメトリローカルログは JSON Lines 形式で、**自動ローテーションやクリーンアップは行われません**。ユーザーはいつでも手動で削除できます：

```bash
rm ~/.autoship/telemetry.logl
```

### 3.2 監査ログ

監査ログはデフォルトで **30 日間**保持し、設定で調整可能です：

```toml
[audit]
retention_days = 30
```

以下のコマンドで期限切れログをクリーンアップ：

```bash
autoship audit cleanup
```

クリーンアップロジックは `mtime` が `retention_days` 日以前の `audit.*.jsonl` ファイルを削除します。

## 4. テレメトリの有効化・無効化

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

`.autoship.toml` に：

```toml
[telemetry]
enabled = true
endpoint = "https://telemetry.autoship.dev/v1/events"
batch_size = 10
timeout = 5.0
allow_untrusted_endpoint = false
```

旧版の `telemetry_enabled = false` も引き続き互換性があり、起動時に自動的に `[telemetry].enabled` に移行されます。

## 5. リモートエンドポイントのセキュリティ

- `https://` エンドポイントのみ受け付け。
- デフォルトでは `telemetry.autoship.dev` への送信のみ許可。
- 他のドメインへ送信するには以下を同時に満たす必要があります：
  - 設定ファイルで `allow_untrusted_endpoint = true` を設定。
  - または環境変数 `AUTOSHIP_TELEMETRY_ALLOW_UNTRUSTED=1` を設定。
- リクエストタイムアウトはデフォルト 5 秒、最大 30 秒まで。

## 6. あなたの権利

- **知る権利**：収集されるすべてのフィールドは本文書と [docs/telemetry.md](telemetry.md) で公開説明。
- **制御権**：テレメトリはデフォルトで無効、ユーザーが完全に制御し、いつでも有効化・無効化可能。
- **監査権**：ローカルのテレメトリと監査ログは平文の JSON Lines で保存され、ユーザーが直接確認可能。
- **削除権利**：ローカルログファイルを手動削除するだけで、収集されたローカルデータをすべて消去可能。

## 7. お問い合わせ

プライバシーに関するご質問は以下までご連絡ください：

- GitHub Issues：[https://github.com/MS33834/autoship-cli/issues](https://github.com/MS33834/autoship-cli/issues)
- メール：team@autoship.dev
