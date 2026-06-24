# metrics

実行時メトリクスを確認します。表示と JSON エクスポートをサポートしています。

## 構文

```bash
autoship metrics [OPTIONS] COMMAND [ARGS]...
```

## 引数

`metrics` コマンド自体は位置引数を受け取りません。サブコマンドで操作します。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | ヘルプ情報を表示して終了 |

## サブコマンド

### metrics show

収集された実行時メトリクスを表示します。

```bash
autoship metrics show [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | JSON 形式で出力 |
| - | `--reset` | `False` | 表示後にメトリクスをリセット |

### metrics export

収集された実行時メトリクスを JSON ファイルにエクスポートします。

```bash
autoship metrics export [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| `-o` | `--output PATH` | `~/.autoship/metrics.json` | メトリクス JSON ファイルの書き込みパス |
| - | `--reset` | `False` | エクスポート後にメトリクスをリセット |

## 例

メトリクスを表示：

```bash
autoship metrics show
```

JSON 形式で表示：

```bash
autoship metrics show --json
```

デフォルトパスにエクスポート：

```bash
autoship metrics export
```

指定パスにエクスポートしてメトリクスをクリア：

```bash
autoship metrics export --output ./metrics.json --reset
```

## 出力の注意点 / よくあるエラー

- `--reset` は収集済みのメトリクスをクリアします。エクスポート前に履歴データの保持が不要であることを確認してください。
- デフォルトのエクスポートパスは `~/.autoship/metrics.json` です。ディレクトリが書き込み可能であることを確認してください。

## 関連コマンド

- [doctor](./doctor.md) — 実行環境をチェック
- [config](./config.md) — 設定を管理
