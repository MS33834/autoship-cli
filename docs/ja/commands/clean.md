---
title: clean
---
# clean

プロジェクトコードをクリーンアップしてフォーマットします。デフォルトのツールチェーンは `autoflake` と `black` で、`.autoship.toml` の `[clean]` セクションでカスタマイズできます。

## 構文

```bash
autoship clean [OPTIONS] [PATHS]...
```

## 引数

| 名前 | 必須 | 説明 |
|---|---|---|
| `paths` | いいえ | クリーンアップ対象のパス。デフォルトは現在のディレクトリ（動的検出） |

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--check` | `False` | 修正が必要な場合は非ゼロの終了コードを返す |
| `-y` | `--yes` | `False` | 対話式の確認をスキップ |

## 例

現在のディレクトリをクリーンアップ：

```bash
autoship clean
```

パスを指定：

```bash
autoship clean src tests
```

CI 環境でフォーマットが必要かチェック：

```bash
autoship clean --check
```

確認をスキップ：

```bash
autoship clean --yes
```

期待される出力例：

```text
reformatted /path/to/project/hello.py

All done! ✨ 🍰 ✨
1 file reformatted.
Clean complete.
```

## 出力の注意点 / よくあるエラー

- `--check` モードでは、ファイルに修正が必要な場合、コマンドは非ゼロの終了コードを返します。CI での使用に適しています。
- 設定されたクリーンアップツールが見つからない場合、インストールの推奨が表示されます。
- `autoflake` / `black` などの外部フォーマットツールが利用できない場合、clean は自動的に内蔵フォーマッタにフォールバックします。

## 内蔵フォーマッタ

外部ツールチェーンが不完全な場合、clean は内蔵フォーマッタを使用して以下のファイルタイプを処理します：

`.py` `.pyi` `.pyx` `.pxd` `.js` `.ts` `.jsx` `.tsx` `.rs` `.go` `.java` `.c` `.cpp` `.h` `.rb`

処理範囲：
- 各行の末尾の空白文字を削除
- 連続する空行を単一の空行に統合
- 行内の 2 つ以上の連続スペースを単一スペースに圧縮（インデントと文字列リテラルは保持）
- ファイルが正確に 1 つの末尾改行で終わるようにする

## 関連コマンド

- [verify](./verify.md) — 検証を実行
- [commit](./commit.md) — 変更をコミット
