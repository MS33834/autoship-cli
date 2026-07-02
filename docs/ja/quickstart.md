---
title: クイックスタート
---
# クイックスタート

> このガイドでは、AutoShip のコアフローを 5 分で体験します。AutoShip はデフォルトでローカル優先です——clean/verify/commit はすべてマシンから外に出ません。

## 前提条件

- Python ≥ 3.10
- [pipx](https://pypa.github.io/pipx/) または [uv](https://docs.astral.sh/uv/)
- Git、かつカレントディレクトリが Git リポジトリであること
- （任意、AI 修正を体験する場合）[Ollama](https://ollama.com/) が実行中であること

## インストール

```bash
pipx install autoship
```

## 5 分で試す AI なし版

```bash
# 1. 設定を初期化
autoship init --yes

# 2. コードをクリーンアップ（不要な import 削除、フォーマット）
autoship clean --yes

# 3. コミットメッセージを生成してコミット
autoship commit

# 4. テストを実行して検証
autoship verify pytest

# 5. アップロードをプレビュー（実際にはアップロードしない）
autoship upload --target pypi --dry-run
```

> `upload --dry-run` はプレビューのみです。実際のアップロードには PyPI 認証情報が必要です。詳しくは [アップロードコマンドリファレンス](commands/upload.md) を参照してください。

## +5 分で試す AI あり版

`verify --fix` の自動修復を体験したい場合：

```bash
# 1. Ollama をインストールして起動し、小規模モデルを取得
ollama pull qwen2.5-coder:1.5b

# 2. AutoShip で Ollama を使用するよう設定（.autoship.toml に記述）
# [model]
# backend = "ollama"

# 3. 検証して自動修復
autoship verify --fix pytest
```

## 次のステップ

- [コマンドリファレンス](commands/index.md)
- [設定説明](configuration.md)
- [モデル設定](models.md)
- [プラグイン開発](plugin-development.md)
