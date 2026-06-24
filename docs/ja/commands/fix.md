# fix

LLM に直近の検証失敗に対する修正提案を生成させます。

## 構文

```bash
autoship fix [OPTIONS] [ERROR_FILE]
```

## 引数

| 名前 | 必須 | 説明 |
|---|---|---|
| `error_file` | いいえ | エラーログのパス。デフォルトは直近の `verify` 出力 |

## オプション

| 短縮 | オプション | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| `-y` | `--yes` | `False` | 確認をスキップ |

## 例

直近の検証失敗のエラーログを使用：

```bash
autoship fix
```

エラーログファイルを指定：

```bash
autoship fix .autoship/error/verify_20250622.log
```

提案を自動適用（`--yes` と併用）：

```bash
autoship fix --yes
```

## 出力の注意点 / よくあるエラー

- エラーログが見つからない場合、先に `autoship verify` を実行するよう促されます。
- 修正提案にはローカルモデルバックエンドが利用可能である必要があります。モデルが起動していない場合は WARNING が表示されます。

## 関連コマンド

- [verify](./verify.md) — 検証を実行してエラーサマリーを生成
- [doctor](./doctor.md) — モデルバックエンドの接続性をチェック
