---
title: デモスクリプトと録画ガイド
---
# デモスクリプトと録画ガイド

このページでは AutoShip-CLI の asciinema デモ録画スクリプトを提供します。スクリプトの内容を保存した後、[asciinema](https://asciinema.org/) を使用して録画し、`website/demo.cast` としてエクスポートできます。

## 推奨録画環境

- ターミナルサイズ：80x24 または 120x30
- フォント：等幅フォント。Fira Code または JetBrains Mono を推奨
- テーマ：ダーク背景、高コントラスト
- 画面クリアコマンド：`clear`

## 録画環境

- Python 3.12
- Ollama 0.5.x
- モデル：`qwen2.5-coder:1.5b`
- OS：Ubuntu 22.04（または macOS 14）

## デモスクリプト

```bash
# 1. ウェルカムとインストール
clear
echo "$ pipx install autoship"
pipx install autoship --quiet 2>/dev/null || echo "(インストール済み)"

# 2. バージョンとヘルプ
clear
echo "$ autoship --version"
autoship --version
echo ""
echo "$ autoship --help"
autoship --help

# 3. プロジェクトの初期化
clear
echo "$ autoship init --yes"
autoship init --yes

# 4. doctor 診断の表示
clear
echo "$ autoship doctor"
autoship doctor

# 5. コードのクリーンアップ
clear
echo "$ autoship clean"
autoship clean --yes

# 6. 検証
clear
echo "$ autoship verify python --version"
autoship verify python --version

# 7. プラグインリスト
clear
echo "$ autoship plugin list"
autoship plugin list

# 8. コミットメッセージの生成（デモモード、実際にはコミットしない）
clear
echo "$ git diff --cached | autoship commit --dry-run"
git diff --cached 2>/dev/null | autoship commit --dry-run || echo "(デモ：staged changes なし)"

# 9. アップロード（デモモード）
clear
echo "$ autoship upload --target pypi --dry-run"
autoship upload --target pypi --dry-run

# 10. 終了
clear
echo "Thanks for trying AutoShip!"
echo ""
echo "  pipx install autoship"
echo "  https://autoship.dev"
```

## 録画コマンド

```bash
# asciinema をインストール
pipx install asciinema

# 録画
cd /workspace/autoship-cli
asciinema rec website/demo.cast --command "bash docs/demo-script.sh"

# 再生して確認
asciinema play website/demo.cast
```

## 公式サイトへの埋め込み

`website/demo.cast` を asciinema.org にアップロードした後、`website/index.html` にプレーヤーを埋め込めます：

```html
<script src="https://asciinema.org/a/xxxxxx.js" id="asciicast-xxxxxx" async></script>
```

またはドキュメントサイトで [mkdocs-asciinema](https://github.com/t6g/mkdocs-asciinema) プラグインを使用します。
