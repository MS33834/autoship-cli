---
title: upload
---
# upload

アーティファクトを設定されたターゲットにアップロードします。PyPI、Docker、GitHub Release をサポートしています。

## 構文

```bash
autoship upload [OPTIONS]
```

## 引数

`upload` コマンドは位置引数を受け取りません。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--target TEXT` | - | アップロードターゲット（例：`pypi`、`docker`、`github`）（必須） |
| - | `--image TEXT` | - | Docker イメージ名 |
| `-t` | `--tag TEXT` | - | Docker イメージタグまたは GitHub release タグ |
| - | `--artifact TEXT` | - | アップロードするアーティファクト。複数回指定可能 |
| - | `--repository TEXT` | `testpypi` | PyPI リポジトリ名 |
| - | `--repository-url TEXT` | - | PyPI リポジトリのアップロード URL |
| - | `--registry TEXT` | - | Docker レジストリプレフィックス（例：`localhost:5000`） |

## 例

PyPI にアップロード：

```bash
autoship upload --target pypi
```

Docker イメージをアップロード：

```bash
autoship upload --target docker --image myapp --tag 0.1.0
```

GitHub Release を公開してアーティファクトをアップロード：

```bash
autoship upload --target github --tag v0.1.0 --artifact dist/*.whl
```

実際にアップロードせずに実行内容をプレビュー：

```bash
autoship --dry-run upload --target pypi
```

## 出力の注意点 / よくあるエラー

- `--dry-run` は実行される操作を表示します。CI での事前確認に適しています。
- Docker アップロードにはローカルの Docker デーモンがアクセス可能である必要があります。
- PyPI アップロードはデフォルトで `testpypi` を使用します。本番環境では `--repository pypi` を明示的に指定してください。

## 関連コマンド

- [commit](./commit.md) — 先にコミットしてからアップロード
- [verify](./verify.md) — アップロード前に検証を実行
