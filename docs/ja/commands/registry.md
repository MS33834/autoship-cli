# registry

プラグインレジストリの分析とリモートインデックスの同期を行います。

## 構文

```bash
autoship registry [OPTIONS] COMMAND [ARGS]...
```

## 引数

`registry` コマンド自体は位置引数を受け取りません。サブコマンドで操作します。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | ヘルプ情報を表示して終了 |

## サブコマンド

### registry list

レジストリ分析ダッシュボードを表示します。

```bash
autoship registry list [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--top INTEGER` | `5` | ランキングに表示するプラグイン数 |

### registry dashboard

レジストリ分析ダッシュボードを表示します（`list` と同じ動作）。

```bash
autoship registry dashboard [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--top INTEGER` | `5` | ランキングに表示するプラグイン数 |

### registry sync

リモートソースからプラグインレジストリインデックスを同期します。

```bash
autoship registry sync [OPTIONS]
```

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| `-o` | `--output PATH` | `~/.autoship/registry/plugins.json` | 同期後のレジストリインデックス出力パス |
| `-f` | `--force` | `False` | ローカルキャッシュを強制上書き |
| - | `--dry-run` | `False` | 変更を表示するが書き込まない |

## 例

レジストリ分析ダッシュボードを表示：

```bash
autoship registry list
```

上位 10 個のプラグインを表示：

```bash
autoship registry list --top 10
```

リモートレジストリインデックスを同期：

```bash
autoship registry sync
```

ローカルキャッシュを強制上書き：

```bash
autoship registry sync --force
```

同期内容をプレビュー：

```bash
autoship registry sync --dry-run
```

## 出力の注意点 / よくあるエラー

- `list` と `dashboard` は現在同じ内容を表示します。
- 同期はデフォルトで `~/.autoship/registry/plugins.json` に書き込まれます。ディレクトリが書き込み可能であることを確認してください。
- ネットワークが利用できない場合 `sync` は失敗します。先に `doctor` のネットワーク診断を確認してください。

## 関連コマンド

- [plugin](./plugin.md) — プラグインのインストール、アンインストール、管理
- [doctor](./doctor.md) — 環境とネットワークをチェック
