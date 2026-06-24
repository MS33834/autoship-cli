# verify

検証コマンドを実行し、失敗時に AI 支援による修正をサポートします。`verify` はエラーサマリーをキャプチャして `.autoship/error/` に保存し、後続の `fix` コマンドで使用できるようにします。

## 構文

```bash
autoship verify [OPTIONS] COMMAND
```

## 引数

| 名前 | 必須 | 説明 |
|---|---|---|
| `command` | はい | 実行する検証コマンド（例：`pytest`、`mypy src`） |

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--fix` | `False` | 失敗時にモデルを呼び出して修正提案を生成 |

## 例

pytest を実行：

```bash
autoship verify pytest
```

引数付きの検証コマンドを実行：

```bash
autoship verify "pytest tests/unit"
```

失敗時に AI 修正提案を要求：

```bash
autoship verify pytest --fix
```

## 出力の注意点 / よくあるエラー

- 検証失敗時は `.autoship/error/` ディレクトリでマスキングされたエラーサマリーを確認できます。
- `--fix` はプラグインの `on_error` Hook をトリガーし、`FixSuggestion` を収集してユーザーにパッチの適用を促します。
- LLM による修正が必要な場合は、ローカルモデルバックエンドが起動し、正しく設定されていることを確認してください。

## 関連コマンド

- [fix](./fix.md) — 直近の検証失敗に対する修正提案を生成
- [doctor](./doctor.md) — モデルバックエンドとツールチェーンをチェック
