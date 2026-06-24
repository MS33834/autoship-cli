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

## 関連コマンド

- [verify](./verify.md) — 検証を実行
- [commit](./commit.md) — 変更をコミット
