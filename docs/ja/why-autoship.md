---
title: AutoShip を選ぶ理由
---
# AutoShip を選ぶ理由

> デリバリー自動化ツールを選ぶ前に、AutoShip と主要ツール（husky / pre-commit / GitHub Actions / commitizen）の違いを把握しましょう。本ページでは、AutoShip が優位でない点も正直に記載し、プロジェクトに合うか判断しやすくします。

## 主要ツールとの比較

| 項目 | AutoShip | husky | pre-commit | GitHub Actions | commitizen |
|---|---|---|---|---|---|
| ローカル優先（デフォルトでオフライン） | ✅ はい | ✅ はい | ⚠️ hook 取得に通信が必要 | ❌ クラウドで実行 | ✅ はい |
| AI によるコミットメッセージ生成 | ✅ 組み込み（ローカル/クラウド選択可） | ❌ なし | ❌ なし | ❌ なし | ⚠️ テンプレート生成のみ、AI ではない |
| コミット前のセキュリティスキャン内蔵 | ✅ はい | ❌ なし（hook 設定が必要） | ⚠️ サードパーティ hook に依存 | ⚠️ 自前構築が必要 | ❌ なし |
| プラグイン拡張 | ✅ pluggy Hook | ⚠️ git hook スクリプトのみ | ✅ hook リポジトリ | ✅ Marketplace | ⚠️ 限定的 |
| 多言語 i18n ドキュメント | ✅ 中/英/日 | ❌ 英語のみ | ❌ 英語のみ | ❌ 英語のみ | ⚠️ 一部翻訳 |
| 設定の複雑さ | 低（`autoship init --yes` 一発） | 低 | 中（`.pre-commit-config.yaml` 必要） | 高（YAML ワークフロー） | 中 |
| ネットワーク必須か | 否（コアコマンドはオフライン可） | 否 | はい（初回 hook 取得） | はい | 否 |
| トリガー タイミング | ローカル手動 / 任意段階 | git hook | git hook | push / PR | 手動 |
| カバレッジ | clean + verify + commit + upload | git hook のみ | 検査のみ | 任意（ただしオンライン） | コミット規約のみ |

## AutoShip が優位なシーン

- **「クリーンアップ → 検証 → コミット → アップロード」を1コマンドで完結させたい**：AutoShip は4ステップを統一フローに連結し、hook や CI を自前で組み立てる必要がありません。
- **コードのプライバシーを重視し、デフォルトでクラウドに送りたくない**：ローカル優先 ＋ ローカル AI モデルを選択可能、コアコマンドはオフラインで動作。
- **実際の diff に基づいて AI がコミットメッセージを生成してほしい**：テンプレート埋めではなく。
- **中国語/日本語チーム**：ネイティブの i18n ドキュメントと CLI プロンプトで導入ハードルを下げます。

## AutoShip が優位でない点（正直な注記）

- **エコシステム規模**：husky / pre-commit は大規模なコミュニティと既成 hook リポジトリを持ちます。AutoShip のプラグインエコシステムはまだ発展途上で、利用可能なサードパーティプラグインは少なめです。
- **実行環境**：AutoShip は Python ≥ 3.10 必須。husky / commitizen のほうが Node エコシステムに友好で、純フロントエンドプロジェクトでは扱いやすい場合があります。
- **CI 連携の成熟度**：GitHub Actions は膨大な公式/コミュニティ Action と安定ホスティングを持ちます。AutoShip の CI 連携はまだ成熟途中です。
- **既存プロジェクトとの互換性**：成熟した `.pre-commit-config.yaml` を持つプロジェクトは AutoShip への移行で一部 hook を書き直す必要があり、短期的な移行コストが発生します。
- **Windows の安定性**：コア機能は Windows をサポートしますが、一部パスのエッジケースが残っています。詳しくは [既知の問題](known-issues.md) を参照。

## 他ツールを選ぶべきとき

- 既存スクリプトを git hook で起動するだけ → **husky** のほうが軽量。
- コードのフォーマット/lint 検査だけが必要で、大規模 hook リポジトリに依存する → **pre-commit** が適任。
- PR 上で複雑な CI マトリクス（複数 OS、複数マトリクス）を動かす必要がある → **GitHub Actions**。
- Conventional Commits 規約を強制したいだけで AI は不要 → **commitizen** で十分。

AutoShip はこれらツールと排他ではありません：CI で GitHub Actions を使いローカルで AutoShip を使う、あるいは AutoShip から pre-commit のチェッカーを呼び出す、といった併用が可能です。

## 次のステップ

- [クイックスタート](quickstart.md)
- [コマンドリファレンス](commands/index.md)
- [プラグイン開発](plugin-development.md)
