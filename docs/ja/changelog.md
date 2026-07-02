---
title: Changelog
---
# Changelog

本文書は [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) 形式に従い、[Semantic Versioning](https://semver.org/lang/ja/) に準拠します。

## [1.0.0] - 2026-06-19

### Added

- 初の安定バージョンをリリース。
- コミュニティヘルスファイルと issue テンプレートを追加し、本番環境からのフィードバック収集を容易に。

### Changed

- `autoship` のバージョン番号を `1.0.0` にアップグレード。
- `autoship-sdk` のバージョン番号を `1.0.0` にアップグレードし、`autoship>=1.0.0` に依存。

### Fixed

- すべての GitHub Actions ワークフローをリポジトリルートディレクトリ基準のパス前提に更新し、以前の `autoship-cli/` サブディレクトリプレフィックスを削除。
- `release.yml` が `autoship-sdk` の PyPI へのビルドと公開を同時に行うように修正。

## [1.0.0-rc.1] - 2026-06-19

### Added

- CLI の国際化（i18n）、英語と中国語をサポート。
  - `--lang zh|en` を使用するか `.autoship.toml` で `locale = "zh"` を設定。
  - システム言語を自動検出し、デフォルトは英語にフォールバック。
- `autoship doctor` 診断コマンド：Python、Git、モデルバックエンド、クリーンツールチェーン、プラグイン依存関係、監査/テレメトリディレクトリの権限をチェック。
- `autoship audit export` と `autoship audit cleanup` コマンド、監査ログの構造化エクスポートと保持期間管理をサポート。
- 公式プラグインレジストリインデックス `src/autoship/registry/plugins.json`、`autoship plugin search` と `autoship plugin install` をサポート。
- `autoship-sdk` プラグイン開発キット（`autoship-sdk/` に配置）：
  - `Plugin` ベースクラスと `hook` デコレータ。
  - `PluginTestHarness` で分離された Hook テスト。
  - `create_plugin` スキャフォールドで新規プラグインプロジェクトを作成。
- `website/` 静的公式サイトと GitHub Pages デプロイワークフロー。
- `.autoship.team.toml` によるチームレベル設定のサポート。
- `AUTOSHIP_*` プレフィックスの環境変数ですべての設定項目を上書き可能。

### Changed

- `autoship` のバージョン番号を `1.0.0-rc.1` にアップグレード。
- `autoship-sdk` のバージョン番号を `1.0.0-rc.1` にアップグレードし、`autoship>=1.0.0rc1` に依存。

### Fixed

- `ollama.py`、`registry_index.py`、`config_center.py`、`hardware_profiler.py`、`hook_dispatcher.py` の mypy/pyright 互換性の問題を修正。

## [0.2.0-beta.1] - 2026-06-18

### Added

- 境界テストとエラー注入でモデル層、Git 層、ツールチェーン層、プラグイン層、ファイル/リソース層をカバー。
- パフォーマンスベンチマークフレームワーク `benchmarks/benchmark.py`、起動時間、clean 実行時間、アイドルメモリなどの指標をサポート。
- CI/CD マルチプラットフォームパッケージング：Linux/macOS/Windows 向けシングルファイル実行可能ファイル、SHA256 チェックサム、SBOM。
- `benchmark.yml` ワークフローが手動トリガーと PR トリガーでパフォーマンス回帰をサポート。
- MkDocs Material ドキュメントサイトと GitHub Pages 自動デプロイ。
- オプションのテレメトリとエラーレポート、デフォルトは無効。コマンド/実行時間/終了コード/例外タイプのみ収集（コード内容は含まない）。

### Fixed

- `OllamaGateway.chat` が HTTP エラー、JSON 解析エラー、タイムアウトを正しく `ModelGatewayError` に変換するように修正。
- `clean` コマンドの `--check` パラメータが直接呼び出し時に実際のブールデフォルト値を使用するように修正。

### Changed

- 開発依存関係に `pyinstaller>=6.0.0` と `mkdocs-material>=9.0.0` を追加。

## [0.1.0] - 2026-06-18

### Added

- AutoShip-CLI コアコマンドを初期化：`init`、`clean`、`commit`、`verify`、`upload`、`plugin`。
- [pluggy](https://pluggy.readthedocs.io/) ベースのプラグインシステム、`pre_*`、`post_*`、`on_error` ライフサイクルフックをサポート。
- ローカル優先の AI モデルルーティング、Ollama、LM Studio、llama.cpp、vLLM バックエンドをサポート。
- ハードウェア認識能力：CPU/GPU/メモリに基づきモデル階層を自動推奨。
- 公式組み込みプラグイン：
  - `security-scan`：コミット前に bandit/gitleaks/osv-scanner セキュリティスキャンを実行。
  - `docker-ship`：`upload --target docker` 時にイメージを自動ビルド/プッシュ。
  - `web-search`：`verify --fix` 失敗時にエラーコンテキストを Web 検索。
- 監査ログシステム、主要な CLI 操作を記録。
- プラグイン信頼レベルとローカルレジストリ管理（`builtin`/`verified`/`community`/`untrusted`）。
- アップロードアダプタが PyPI、Docker、GitHub をサポート。
- エンドツーエンド（E2E）テストと境界シナリオのカバー。
- パフォーマンスベンチマークと結果記録（`benchmarks/`）。
- 完全な中国語 MkDocs Material ドキュメントサイト。
- GitHub Actions ドキュメント自動デプロイワークフロー。

### Changed

- Typer CLI エントリとグローバルオプション（`--verbose`、`--dry-run`、`--yes`、`--config`）を統一。
- Pydantic を使用して `.autoship.toml` 設定モデルを定義。

### Security

- セキュリティスキャンに bandit と pip-audit を統合。
- 資格情報はデフォルトでログに書き込まれない。
- プラグインは Hook メカニズムで実行され、最小権限の原則に従う。

[1.0.0]: https://github.com/MS33834/autoship-cli/releases/tag/v1.0.0
[1.0.0-rc.1]: https://github.com/MS33834/autoship-cli/releases/tag/v1.0.0-rc.1
[0.2.0-beta.1]: https://github.com/MS33834/autoship-cli/releases/tag/v0.2.0-beta.1
[0.1.0]: https://github.com/MS33834/autoship-cli/releases/tag/v0.1.0
