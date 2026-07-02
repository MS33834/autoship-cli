# AutoShip-CLI Delivered Features

<p align="right">
  <strong>English</strong> |
  <a href="#中文">中文</a> |
  <a href="#日本語">日本語</a>
</p>

> This document summarizes what AutoShip-CLI has delivered as of the end of the
> P4-1 milestone (version `1.0.0`). The forward-looking roadmap lives in
> [`PLAN.md`](./PLAN.md). Progress is mirrored in [`CHANGELOG.md`](./CHANGELOG.md).

---

## English

AutoShip-CLI is a **local-first intelligent delivery janitor**: it cleans,
verifies, commits, and ships project artifacts without sending source code to
the cloud. Everything below is shipped, tested, and covered by the quality
gate (`ruff` + `pyright` strict + `pytest` ≥85% coverage + `bandit`).

### Core CLI surface

- Commands: `init`, `clean`, `commit`, `verify` (with `--fix`), `upload`,
  `plugin`, `doctor`, `config`, `registry`, `metrics`, `audit export|cleanup`.
- Global options: `--verbose`, `--dry-run`, `--yes`, `--config`, `--lang zh|en|ja`.
- Built on Typer + Pydantic, packaged as a `uv` workspace
  (`autoship` + `autoship-sdk`).

### Local-first AI model routing

- Backends: Ollama, LM Studio, llama.cpp, vLLM, OpenAI, Azure OpenAI,
  OpenRouter — all behind a unified `ModelRouter` with automatic fallback.
- Hardware-aware tier recommendations (CPU/GPU/memory) pick a sensible local
  model out of the box.
- Every provider error is redacted so backend URLs, API keys, and absolute
  local paths never leak into prompts, logs, or user-facing messages.

### Plugin system

- [pluggy](https://pluggy.readthedocs.io/)-based hooks: `pre_*`, `post_*`,
  `on_error` lifecycle.
- Trust levels (`verified` / `community`), permission declarations, and a
  JSON-Schema-validated registry (`registry/plugins.json` + `registry/schema.json`).
- Built-in plugins: `security-scan`, `docker-ship`, `web-search`, `typecheck`.
- `autoship-sdk` provides `Plugin` base class, `@hook` decorator,
  `PluginTestHarness`, and a `create_plugin` scaffold.

### Security & compliance hardening

- **ToolVerifier**: every external tool (`git`, `docker`, `twine`, `gh`,
  `patch`) is resolved by absolute path and optional SHA-256 hash, blocking
  PATH pollution attacks across `commit` / `upload` / `verify` / `fix`.
- **Redaction pipeline**: `redaction.redact_text` masks tokens/keys by name
  and value pattern; `redaction.redact_paths` strips absolute project-root
  and home-directory prefixes before any prompt is sent to a remote model.
- Registry index signatures + plugin sha256/signature verification on
  install/update.
- Audit log redaction, SIEM forwarding with failure circuit-breaker,
  `0o600`/`0o700` file permissions on all persisted state.
- Editor allowlist for `commit`, file-path + extension allowlist for `fix`,
  env-var override allowlist for `ConfigCenter`, HTTPS-only telemetry
  endpoint validation.

### Distribution & CI

- PyPI / Docker / GitHub upload adapters with `--dry-run` and
  `--repository-url` (TestPyPI by default).
- `uv build` produces wheel + sdist; `autoship-sdk` is published alongside.
- GitHub Actions: `ci.yml`, `nightly.yml` (multi-OS PyInstaller binaries +
  SHA256 + SBOM + benchmark), `release.yml` (TestPyPI/PyPI routing + automatic
  `CHANGELOG.md` generation via `scripts/release_changelog.py`),
  `benchmark.yml`.
- SemVer + Keep a Changelog, automated release notes.

### Documentation & i18n

- MkDocs Material site, fully translated into **Chinese / English / Japanese**
  (`docs/`, `docs/en/`, `docs/ja/`).
- Per-command reference pages, plugin development & publishing guides,
  privacy policy, telemetry docs, release checklist, security audit.
- CLI strings localized via `--lang zh|en|ja` with locale parity tests.

### Telemetry & privacy

- Opt-in by default; collects only command name, duration, exit code, and
  exception type — never source code.
- PII filter (keys, paths, emails, JWTs, hashes/tokens); 30-day audit log
  retention with `autoship audit cleanup`.

### Quality posture

- **670+ tests passing**, 17 skipped (tool-missing integration tests),
  **87.88% coverage**.
- `ruff check` + `ruff format --check` clean across 156 files.
- `pyright` strict mode, 0 errors. `bandit -ll` and `pip-audit` clean.

---

## 中文

AutoShip-CLI 是一款**本地优先的智能交付助手**：清理、验证、提交、上传全流程默认在本地完成，源码不离开你的机器。以下能力均已交付、测试通过，并通过质量门禁（`ruff` + `pyright` strict + `pytest` 覆盖率 ≥85% + `bandit`）。

### 核心 CLI

- 命令：`init`、`clean`、`commit`、`verify`（含 `--fix`）、`upload`、`plugin`、`doctor`、`config`、`registry`、`metrics`、`audit export|cleanup`。
- 全局选项：`--verbose`、`--dry-run`、`--yes`、`--config`、`--lang zh|en|ja`。
- 基于 Typer + Pydantic，以 `uv` workspace 组织（`autoship` + `autoship-sdk`）。

### 本地优先的 AI 模型路由

- 后端：Ollama、LM Studio、llama.cpp、vLLM、OpenAI、Azure OpenAI、OpenRouter，统一由 `ModelRouter` 调度并支持自动 fallback。
- 硬件感知分级推荐（CPU/GPU/内存），开箱即用选合适本地模型。
- 所有 provider 错误均脱敏，后端 URL、API key、绝对本地路径不会泄露到 prompt、日志或用户提示。

### 插件系统

- 基于 [pluggy](https://pluggy.readthedocs.io/) 的 `pre_*`/`post_*`/`on_error` 生命周期 Hook。
- 信任级别（`verified`/`community`）、权限声明、JSON Schema 校验的注册表（`registry/plugins.json` + `registry/schema.json`）。
- 内置插件：`security-scan`、`docker-ship`、`web-search`、`typecheck`。
- `autoship-sdk` 提供 `Plugin` 基类、`@hook` 装饰器、`PluginTestHarness`、`create_plugin` 脚手架。

### 安全与合规加固

- **ToolVerifier**：`git`/`docker`/`twine`/`gh`/`patch` 等外部工具按绝对路径 + 可选 SHA-256 哈希解析，贯穿 `commit`/`upload`/`verify`/`fix`，阻断 PATH 污染攻击。
- **脱敏管线**：`redact_text` 按键名与值模式遮蔽 token/key；`redact_paths` 在 prompt 发往远端模型前剥离项目根与家目录的绝对路径前缀。
- 注册表索引签名校验 + 插件安装/更新时 sha256/签名校验。
- 审计日志脱敏、SIEM 转发失败熔断、所有持久化文件 `0o600`/目录 `0o700`。
- `commit` 编辑器白名单、`fix` 路径与扩展名白名单、`ConfigCenter` 环境变量覆盖白名单、遥测端点 HTTPS 校验。

### 分发与 CI

- PyPI / Docker / GitHub 上传适配器，支持 `--dry-run` 与 `--repository-url`（默认 TestPyPI）。
- `uv build` 产出 wheel + sdist；`autoship-sdk` 同步发布。
- GitHub Actions：`ci.yml`、`nightly.yml`（多平台 PyInstaller 单文件 + SHA256 + SBOM + benchmark）、`release.yml`（TestPyPI/PyPI 路由 + 由 `scripts/release_changelog.py` 自动生成 `CHANGELOG.md`）、`benchmark.yml`。
- SemVer + Keep a Changelog，自动 Release Notes。

### 文档与国际化

- MkDocs Material 文档站，**中/英/日**三语完整翻译（`docs/`、`docs/en/`、`docs/ja/`）。
- 各命令独立参考页、插件开发与发布指南、隐私政策、遥测说明、发布 checklist、安全审计。
- CLI 字符串通过 `--lang zh|en|ja` 本地化，并配有 locale 键集一致性测试。

### 遥测与隐私

- 默认 opt-in；仅收集命令名、耗时、退出码、异常类型，绝不收集源码。
- PII 过滤（键名、路径、邮箱、JWT、哈希/token）；审计日志默认保留 30 天，可用 `autoship audit cleanup` 清理。

### 质量基线

- **670+ 测试通过**，17 跳过（工具缺失的集成测试），**覆盖率 87.88%**。
- `ruff check` + `ruff format --check` 156 文件全清。
- `pyright` strict 模式 0 错误；`bandit -ll` 与 `pip-audit` 清洁。

---

## 日本語

AutoShip-CLI は**ローカルファーストのインテリジェントなデリバリー助手**です。クリーン・検証・コミット・アップロードの全工程をデフォルトでローカル完結し、ソースコードをクラウドに送信しません。以下の機能はすべて出荷済み・テスト済みで、品質ゲート（`ruff` + `pyright` strict + `pytest` カバレッジ ≥85% + `bandit`）を通過しています。

### 主要 CLI

- コマンド：`init`、`clean`、`commit`、`verify`（`--fix` 付き）、`upload`、`plugin`、`doctor`、`config`、`registry`、`metrics`、`audit export|cleanup`。
- グローバルオプション：`--verbose`、`--dry-run`、`--yes`、`--config`、`--lang zh|en|ja`。
- Typer + Pydantic 製、`uv` workspace で構成（`autoship` + `autoship-sdk`）。

### ローカルファーストの AI モデルルーティング

- バックエンド：Ollama、LM Studio、llama.cpp、vLLM、OpenAI、Azure OpenAI、OpenRouter。`ModelRouter` で統一し自動フォールバック対応。
- ハードウェア対応のティア推奨（CPU/GPU/メモリ）で適切なローカルモデルを自動選択。
- すべての provider エラーはマスキングされ、バックエンド URL・API キー・絶対ローカルパスはプロンプト・ログ・ユーザー向けメッセージに漏れません。

### プラグインシステム

- [pluggy](https://pluggy.readthedocs.io/) ベースの `pre_*`/`post_*`/`on_error` ライフサイクルフック。
- 信頼レベル（`verified`/`community`）、権限宣言、JSON Schema 検証済みレジストリ（`registry/plugins.json` + `registry/schema.json`）。
- 組み込みプラグイン：`security-scan`、`docker-ship`、`web-search`、`typecheck`。
- `autoship-sdk` が `Plugin` 基底クラス、`@hook` デコレータ、`PluginTestHarness`、`create_plugin` スキャフォールドを提供。

### セキュリティとコンプライアンス強化

- **ToolVerifier**：`git`/`docker`/`twine`/`gh`/`patch` などの外部ツールを絶対パス + 任意の SHA-256 ハッシュで解決し、`commit`/`upload`/`verify`/`fix` 全経路で PATH 汚染攻撃を遮断。
- **マスキングパイプライン**：`redact_text` はキー名と値パターンでトークン/キーを遮蔽、`redact_paths` はプロンプトがリモートモデルに送信される前にプロジェクトルートとホームディレクトリの絶対パス接頭辞を除去。
- レジストリインデックス署名検証 + プラグイン インストール/更新時の sha256/署名検証。
- 監査ログのマスキング、SIEM 転送失敗時のサーキットブレーカー、全永続ファイル `0o600`/ディレクトリ `0o700`。
- `commit` エディタ許可リスト、`fix` パス・拡張子許可リスト、`ConfigCenter` 環境変数上書き許可リスト、テレメトリエンドポイントの HTTPS 検証。

### 配布と CI

- PyPI / Docker / GitHub アップロードアダプタ、`--dry-run` と `--repository-url` 対応（デフォルトは TestPyPI）。
- `uv build` で wheel + sdist を生成、`autoship-sdk` も同時公開。
- GitHub Actions：`ci.yml`、`nightly.yml`（マルチプラットフォーム PyInstaller 単体ファイル + SHA256 + SBOM + ベンチマーク）、`release.yml`（TestPyPI/PyPI ルーティング + `scripts/release_changelog.py` による `CHANGELOG.md` 自動生成）、`benchmark.yml`。
- SemVer + Keep a Changelog、自動リリースノート。

### ドキュメントと i18n

- MkDocs Material ドキュメントサイト、**中/英/日**の三言語へ完全翻訳（`docs/`、`docs/en/`、`docs/ja/`）。
- コマンド別リファレンス、プラグイン開発・公開ガイド、プライバシーポリシー、テレメトリ説明、リリースチェックリスト、セキュリティ監査。
- CLI 文字列は `--lang zh|en|ja` でローカライズ、locale キー集合のパリティテスト付き。

### テレメトリとプライバシー

- デフォルトで opt-in。コマンド名・所要時間・終了コード・例外タイプのみ収集し、ソースコードは収集しません。
- PII フィルタ（キー名・パス・メール・JWT・ハッシュ/トークン）。監査ログはデフォルトで 30 日保持、`autoship audit cleanup` で整理。

### 品質ベースライン

- **670+ テスト合格**、17 スキップ（ツール不足の統合テスト）、**カバレッジ 87.88%**。
- `ruff check` + `ruff format --check` 156 ファイル全クリーン。
- `pyright` strict モード 0 エラー、`bandit -ll` と `pip-audit` クリーン。
