---
title: plugin
---
# plugin

プラグインを管理します。登録済みプラグインのリスト表示、レジストリの検索、インストール/アンインストール、評価、信頼レベルの更新などが含まれます。

## 構文

```bash
autoship plugin [OPTIONS] COMMAND [ARGS]...
```

## 引数

`plugin` コマンド自体は位置引数を受け取りません。サブコマンドで操作します。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | ヘルプ情報を表示して終了 |

## サブコマンド

### plugin list

登録済みプラグインとその信頼レベルをリスト表示します。

```bash
autoship plugin list
```

### plugin search

公式プラグインレジストリインデックスでプラグインを検索します。

```bash
autoship plugin search [OPTIONS] [KEYWORD]
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `keyword` | いいえ | プラグイン名または説明で検索するキーワード |

### plugin info

レジストリ内の特定のプラグインの詳細情報を表示します。

```bash
autoship plugin info [OPTIONS] NAME
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `name` | はい | プラグイン名 |

### plugin install

プラグインパッケージをインストールしてローカルに登録します。

```bash
autoship plugin install [OPTIONS] SOURCE
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `source` | はい | パッケージ記述子またはレジストリ内のプラグイン名 |

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--name TEXT` | - | 登録時に使用するプラグイン名 |
| - | `--version TEXT` | - | プラグインのバージョン |
| - | `--trust LEVEL` | - | 初期信頼レベル：`builtin`、`verified`、`community`、`untrusted` |
| - | `--dry-run` | `False` | 操作のプレビューのみ |
| `-y` | `--yes` | `False` | 確認をスキップ |
| - | `--skip-trust-check` | `False` | 信頼レベルの警告をスキップ |
| - | `--no-sandbox` | `False` | サンドボックスを使用せずに pip install を実行 |

### plugin uninstall

プラグインパッケージをアンインストールし、ローカルレジストリから削除します。

```bash
autoship plugin uninstall [OPTIONS] NAME
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `name` | はい | アンインストールするプラグイン名 |

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--dry-run` | `False` | 操作のプレビューのみ |
| `-y` | `--yes` | `False` | 確認をスキップ |

### plugin rate

登録済みプラグインを評価します。

```bash
autoship plugin rate [OPTIONS] NAME SCORE
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `name` | はい | プラグイン名 |
| `score` | はい | 評価スコア（1〜5） |

### plugin stats

ローカルプラグインの使用統計を表示します。

```bash
autoship plugin stats
```

### plugin trust

登録済みプラグインの信頼レベルを更新します。

```bash
autoship plugin trust [OPTIONS] NAME LEVEL
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `name` | はい | プラグイン名 |
| `level` | はい | 新しい信頼レベル：`builtin`、`verified`、`community`、`untrusted` |

### plugin update

プラグインの更新を確認してインストールします。

```bash
autoship plugin update [OPTIONS] [NAME]
```

| 名前 | 必須 | 説明 |
|---|---|---|
| `name` | いいえ | 更新するプラグイン名 |

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--all` | `False` | すべての登録済みプラグインを更新 |
| - | `--dry-run` | `False` | 操作のプレビューのみ |
| `-y` | `--yes` | `False` | 確認をスキップ |
| - | `--skip-trust-check` | `False` | 信頼レベルの警告をスキップ |
| - | `--no-sandbox` | `False` | サンドボックスを使用せずに pip install を実行 |

## 例

登録済みプラグインをリスト表示：

```bash
autoship plugin list
```

レジストリを検索：

```bash
autoship plugin search docker
```

プラグインの詳細を表示：

```bash
autoship plugin info docker-ship
```

レジストリからプラグインをインストール：

```bash
autoship plugin install docker-ship
```

ローカルプラグインをインストールし、信頼レベルを指定：

```bash
autoship plugin install ./local-plugin --trust verified
```

プラグインの信頼レベルを調整：

```bash
autoship plugin trust my-plugin verified
```

プラグインをアンインストール：

```bash
autoship plugin uninstall my-plugin
```

すべてのプラグインを更新：

```bash
autoship plugin update --all
```

## 出力の注意点 / よくあるエラー

- 信頼レベル：`builtin` > `verified` > `community` > `untrusted`。
- 未検証のプラグインをインストールすると信頼警告が表示されます。`--skip-trust-check` でスキップできます。
- `--no-sandbox` は pip インストールのサンドボックスを無効にします。信頼できる環境でのみ使用してください。

## 関連コマンド

- [registry](./registry.md) — プラグインレジストリの参照と同期
- [doctor](./doctor.md) — プラグインの外部依存関係をチェック
