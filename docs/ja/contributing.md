---
title: コントリビュート
---
## リポジトリの説明

**本リポジトリは GitHub をメインとし、GitCode をミラーとしています。**

- メインリポジトリ：https://github.com/MS33834/autoship-cli
- GitCode ミラー：https://gitcode.com/badhope/autoship-cli

Issue と Pull Request は **GitHub メインリポジトリ** に直接提出してください。GitCode はコードミラーのみに使用し、Issue/PR は処理しません。

---

# 貢献ガイド

AutoShip-CLI への関心ありがとうございます！コミュニティからの貢献を歓迎し、奨励しています。

## 行動規範

本プロジェクトに参加することは、当社の[行動規範](https://github.com/MS33834/autoship-cli/blob/main/CODE_OF_CONDUCT.md)に従うことに同意したものとみなされます。

## 貢献方法

- バグ報告：GitHub Issues を使用し、再現手順、環境情報、最小再現例を添付してください。
- 提案：GitHub Discussions でアイデアを共有してください。
- コード提出：リポジトリをフォークし、フィーチャーブランチを作成し、Pull Request を提出してください。

## 開発環境

本プロジェクトは [uv](https://docs.astral.sh/uv/) で依存関係を管理しています。

```bash
uv sync --all-extras --dev
uv run pytest
```

## コード規範

- [ruff](https://docs.astral.sh/ruff/) でフォーマットと lint を行います。
- [pyright](https://microsoft.github.io/pyright/) で厳格な型チェックを行います。
- コミットメッセージは英語で、[Conventional Commits](https://www.conventionalcommits.org/) 規範に従います。
- 新機能にはテストが必須で、カバレッジ 85% 以上を維持してください。

## Pull Request の提出

1. すべてのチェックがパスすることを確認：`uv run ruff check src tests`、`uv run pyright`、`uv run pytest`。
2. セキュリティスキャンを実行：`uv run bandit -r src -ll`。
3. PR の説明に変更理由、影響範囲、テスト方法を記載。
4. メンテナーのレビューを待ち、必要に応じて修正を行う。

## Registry へのプラグイン提出

サードパーティプラグインを歓迎します！以下のフローで提出してください：

1. [`autoship-sdk`](https://pypi.org/project/autoship-sdk/) を使用してプラグインプロジェクトを作成し、PyPI に公開。
2. GitHub で **Plugin Submission** テンプレートを選択して issue を作成。
3. メンテナーが以下のチェックリストで審査：
   - プラグインが AutoShip hook spec に従い、未認可の操作を行わない。
   - README、オープンソースライセンス、基本テストを含む。
   - 名称が既存プラグインと競合せず、`autoship-*` の命名規則に合致。
   - `verified` を申請する場合は SHA256 チェックサムまたは GPG 署名を提供。
4. 審査通過後、プラグインは `src/autoship/registry/plugins.json` に追加され、
   [Plugin Registry Web UI](https://autoship-cli.github.io/autoship-registry/) に自動的に表示されます。

## ライセンス

コードを貢献することで、貢献した内容がプロジェクトと同じ [MIT](https://github.com/MS33834/autoship-cli/blob/main/LICENSE) ライセンスで提供されることに同意したものとみなされます。
