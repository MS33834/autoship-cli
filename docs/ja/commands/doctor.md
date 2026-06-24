# doctor

現在の環境が AutoShip の実行要件を満たしているか診断します。

## 構文

```bash
autoship doctor [OPTIONS]
```

## 引数

`doctor` コマンドは位置引数を受け取りません。

## オプション

| 短縮 | 長い形式 | デフォルト | 説明 |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | 診断レポートを JSON 形式で出力 |
| - | `--fail-on-error` | `False` | ERROR が存在する場合に非ゼロの終了コードを返す |

## 例

通常の診断を実行：

```bash
autoship doctor
```

構造化出力：

```bash
autoship doctor --json
```

CI ヘルスチェック：

```bash
autoship doctor --fail-on-error
```

## 出力の注意点 / よくあるエラー

- チェック項目：Python バージョン、Git 設定、モデルバックエンドの接続性、クリーンツールチェーン、プラグインの外部依存関係、監査/テレメトリディレクトリの権限など。
- 出力は `OK` / `WARNING` / `ERROR` のレベル別に分かれます。
- ローカルモデル（Ollama/LM Studio）が起動していない場合、`model-backend` は WARNING を表示します。これは正常な動作であり、非 AI コマンドには影響しません。

## 関連コマンド

- [init](./init.md) — プロジェクト設定を初期化
- [verify](./verify.md) — 検証を実行
