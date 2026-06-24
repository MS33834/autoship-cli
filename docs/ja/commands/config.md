# config

AutoShip 設定の確認と管理を行います。有効な設定、個別の設定項目、テレメトリの切り替えが含まれます。

## 構文

```bash
autoship config [OPTIONS] COMMAND [ARGS]...
```

## 引数

`config` コマンド自体は位置引数を受け取りません。サブコマンドで操作します。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | ヘルプ情報を表示して終了 |

## サブコマンド

### config list

有効な設定を表示します（機密値はマスキングされます）。

```bash
autoship config list [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | JSON 形式で出力 |

### config get

単一の設定値を取得します。

```bash
autoship config get [OPTIONS] KEY
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `key` | はい | ドット区切りの設定キー（例：`model.default_tier`） |

### config telemetry

テレメトリ設定の有効化、無効化、または確認を行います。

```bash
autoship config telemetry [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--enable` | `False` | テレメトリを有効化 |
| - | `--disable` | `False` | テレメトリを無効化 |
| - | `--status` | `False` | 現在のテレメトリ状態を表示 |

## 例

有効な設定をリスト表示：

```bash
autoship config list
```

JSON 形式で確認：

```bash
autoship config list --json
```

単一の設定値を取得：

```bash
autoship config get model.default_tier
```

テレメトリ状態を確認：

```bash
autoship config telemetry --status
```

テレメトリを有効化：

```bash
autoship config telemetry --enable
```

テレメトリを無効化：

```bash
autoship config telemetry --disable
```

## 出力の注意点 / よくあるエラー

- `config list` は機密値（API key など）をマスキング処理します。
- テレメトリはデフォルトで無効であり、明示的に有効化した場合のみ匿名の使用データが送信されます。
- 設定は `.autoship.toml`、環境変数（ホワイトリスト内）、コマンドラインオプションで上書きできます。

## 関連コマンド

- [init](./init.md) — 設定ファイルを初期化
- [doctor](./doctor.md) — 設定と環境をチェック
