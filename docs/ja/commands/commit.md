---
title: commit
---
# commit

コミットメッセージを生成して Git コミットを実行します。`-m` を指定しない場合、AutoShip はローカルモデルを呼び出し、diff と stats に基づいて Conventional Commits スタイルのコミットメッセージを生成します。

## 構文

```bash
autoship commit [OPTIONS]
```

## 引数

`commit` コマンドは位置引数を受け取りません。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| `-m` | `--message TEXT` | - | 指定されたコミットメッセージを直接使用 |
| - | `--edit / --no-edit` | `edit` | 生成されたメッセージをエディタで確認するかどうか |

## 例

変更をステージしてコミットメッセージを生成：

```bash
autoship commit
```

コミットメッセージを直接指定：

```bash
autoship commit -m "fix: resolve upload timeout"
```

エディタでの確認をスキップ：

```bash
autoship commit --no-edit
```

## 出力の注意点 / よくあるエラー

- `-m` 使用時は AI を呼び出さず、指定されたメッセージで直接コミットします。
- モデルが未設定の場合、手動でコミットメッセージを編集するよう促されます。
- コミット前に `pre_commit` Hook が実行され、プラグインで拡張できます。

## 関連コマンド

- [clean](./clean.md) — コードをクリーンアップ
- [verify](./verify.md) — 変更を検証
- [upload](./upload.md) — コミット後にアーティファクトをアップロード
