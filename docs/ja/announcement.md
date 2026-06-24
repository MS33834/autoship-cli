# 1.0.0 リリース告知

## 日本語告知

**AutoShip-CLI 1.0.0 正式リリース**

AutoShip-CLI の初の安定版が正式に公開されましたことをお知らせします！AutoShip はローカル優先、AI 支援のコードデリバリーツールチェーンであり、コードベースをクラウドにアップロードすることなく、クリーンアップ、検証、コミット、ビルド、公開を完了できます。

### 主なハイライト

- **ローカル AI**：デフォルトで Ollama、LM Studio などのローカルモデルバックエンドをサポートし、コードは常にローカルに保持。
- **スマートコミット**：diff に基づき Conventional Commits 規範に準拠したコミットメッセージを自動生成。
- **プラグインエコシステム**：セキュリティスキャン、Docker ビルド、Web 検索などのプラグインを組み込みで提供し、コミュニティプラグインの拡張をサポート。
- **エンタープライズ対応**：チーム設定、監査ログ、SIEM 転送、テレメトリホワイトリスト、プライバシーコンプライアンス。
- **多言語 CLI**：英語と中国語インターフェースをサポート。

### クイックスタート

```bash
pipx install autoship
autoship init
autoship clean
autoship commit
autoship verify pytest
```

### リンク

- 公式サイト：<https://ms33834.github.io/autoship-cli/>
- ドキュメント：<https://ms33834.github.io/autoship-cli/docs>
- GitHub：<https://github.com/MS33834/autoship-cli>
- プラグインレジストリ：<https://ms33834.github.io/autoship-cli/registry>

---

## English Announcement

**AutoShip-CLI 1.0.0 is now available**

We are excited to announce the first stable release of AutoShip-CLI, a local-first, AI-assisted code shipping toolkit. AutoShip helps you clean, verify, commit, build, and ship code without uploading your codebase to the cloud.

### Highlights

- **Local AI**: Works with Ollama, LM Studio, and other local model backends by default.
- **Smart commits**: Generate Conventional Commits messages from staged changes.
- **Plugin ecosystem**: Built-in security scans, Docker shipping, web search, and community plugins.
- **Enterprise ready**: Team configs, structured audit logs, SIEM forwarding, telemetry allowlists, and privacy compliance.
- **Multi-language CLI**: English and Chinese interfaces supported.

### Quick start

```bash
pipx install autoship
autoship init
autoship clean
autoship commit
autoship verify pytest
```

### Links

- Website: <https://ms33834.github.io/autoship-cli/>
- Docs: <https://ms33834.github.io/autoship-cli/docs>
- GitHub: <https://github.com/MS33834/autoship-cli>
- Plugin Registry: <https://ms33834.github.io/autoship-cli/registry>

---

## ソーシャルメディア文案

### Twitter / X

```text
🚀 AutoShip-CLI 1.0.0 is out!

Local-first, AI-assisted code shipping for Python teams.

✅ Local models (Ollama, LM Studio)
✅ Smart conventional commits
✅ Plugin ecosystem
✅ Enterprise audit & privacy controls

pipx install autoship

https://ms33834.github.io/autoship-cli/
#AI #DevTools #OpenSource
```

### Weibo / Zhihu

```text
🚀 AutoShip-CLI 1.0.0 正式发布！

一款本地优先、AI 辅助的代码交付工具链：
- 默认本地模型，代码不上云
- 自动生成符合规范的提交信息
- 插件生态（安全扫描、Docker、联网搜索等）
- 企业级审计、遥测与隐私合规

pipx install autoship 即可体验。

官网：https://ms33834.github.io/autoship-cli/
文档：https://ms33834.github.io/autoship-cli/docs
```

### LinkedIn

```text
We just shipped AutoShip-CLI 1.0.0 — a local-first, AI-assisted toolkit for cleaning, verifying, committing, and shipping code.

Key features:
• Local model support (Ollama, LM Studio, vLLM, etc.)
• AI-generated conventional commits
• Extensible plugin system with built-in security scans
• Team configs, audit logs, and privacy-first telemetry

Try it: pipx install autoship
Read more: https://ms33834.github.io/autoship-cli/
```

---

## リリースメールテンプレート

**件名**：AutoShip-CLI 1.0.0 正式リリース

本文：

```text
Hi all,

AutoShip-CLI 1.0.0 初の安定版がリリースされました。

AutoShip はローカル優先、AI 支援のコードデリバリーツールチェーンであり、コードを漏洩させることなく、コミット、検証、ビルド、公開の効率を向上させることを目的としています。

主な特徴：
- ローカル AI モデルサポート（Ollama / LM Studio / vLLM など）
- スマートコミットメッセージ生成
- 組み込みのセキュリティスキャン、Docker ビルド、Web 検索プラグイン
- プラグインレジストリとコミュニティ拡張
- チーム設定、監査ログ、プライバシーコンプライアンス対応テレメトリ

インストール方法：pipx install autoship
ドキュメント：https://ms33834.github.io/autoship-cli/docs
GitHub：https://github.com/MS33834/autoship-cli

ぜひお試しいただき、フィードバックをお寄せください。

AutoShip Team
```
