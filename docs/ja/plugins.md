---
title: プラグイン
---
# プラグイン

AutoShip-CLI は [pluggy](https://pluggy.readthedocs.io/) を採用してプラグインアーキテクチャを実現しています。プラグインはライフサイクルフック（Hooks）を宣言することでコマンドの動作を拡張します。例えば、`verify` の実行前に追加チェックを行ったり、コマンド失敗時に AI 修正提案を提示したりできます。

## 公式組み込みプラグイン

### security-scan

`pre_commit` フェーズで `bandit`/`gitleaks`/`osv-scanner` などのセキュリティチェックを実行し、閾値に達する問題を発見した場合はコミットをブロックします。

```toml
[security]
enabled = true
tools = ["bandit"]
threshold = "medium"
fail_fast = true
```

```bash
autoship commit
# security-scan が中危険以上の問題を発見した場合、コミットは中止されます
```

### docker-ship

`autoship upload --target docker` の前後で Docker イメージの自動ビルド/プッシュを行います。

```toml
[docker_ship]
enabled = true
default_image = "myapp"
default_tag = "latest"
push = true
```

```bash
autoship upload --target docker --image myapp --tag 0.1.0
```

### web-search

`verify --fix` が失敗し、設定で `web_search.enabled = true` の場合、エラーコンテキストを Web 検索して修正提案の生成を支援します。デフォルトは無効です。

```toml
[web_search]
enabled = true
provider = "duckduckgo"
max_results = 3
```

```bash
autoship verify pytest --fix
```

!!! warning "プライバシーに関する注意"
    `web-search` を有効にすると、エラーサマリーが公開検索サービスに送信されます。有効にする前にこの情報の共有に同意していることを確認してください。

## プラグイン管理 CLI

AutoShip にはプラグイン管理コマンドが組み込まれており、サードパーティプラグインの確認、インストール、設定が簡単に行えます：

```bash
# 登録済みプラグインをリスト表示
autoship plugin list

# プラグインをインストール（PyPI パッケージ名、ローカルパス、git URL をサポート）
autoship plugin install my-plugin

# プラグインの信頼レベルを調整
autoship plugin trust my-plugin verified

# プラグインをアンインストール
autoship plugin uninstall my-plugin
```

信頼レベルは `builtin`、`verified`、`community`、`untrusted` の 4 段階です。デフォルトでインストールされるサードパーティプラグインは `community` です。ソースコードをレビューした後に `verified` に昇格することを推奨します。

## 利用可能なフック

すべてのフックは `autoship.hookspec.AutoShipHookSpec` で定義されています：

| フック名 | トリガー タイミング | 戻り値 |
|---|---|---|
| `pre_init` | `autoship init` が設定ファイルを書き込む前 | `None` |
| `post_init` | `autoship init` が設定ファイルを書き込んだ後 | `None` |
| `pre_clean` | `autoship clean` がクリーンツールを実行する前 | `None` |
| `post_clean` | `autoship clean` がクリーンツールを実行した後 | `None` |
| `pre_commit` | `autoship commit` がコミットメッセージを生成する前 | `None` |
| `post_commit` | `autoship commit` が完了した後 | `None` |
| `pre_verify` | `autoship verify` が検証コマンドを実行する前 | `None` |
| `post_verify` | `autoship verify` が完了した後 | `None` |
| `pre_upload` | `autoship upload` がアーティファクトを公開する前 | `None` |
| `post_upload` | `autoship upload` が完了した後 | `None` |
| `on_error` | コマンド実行時に例外がスローされた時 | `FixSuggestion \| None` |

`on_error` は戻り値を返すことが許可された唯一のフックです。コマンドが `--fix` フラグ付きで失敗した場合、AutoShip はすべての `FixSuggestion` を収集し、ユーザーに表示してオプションでパッチを適用できます。

## カスタムプラグインの開発

プラグインの作成、パッケージ化、登録、テスト方法については [プラグイン開発ガイド](plugin-development.md) を参照してください。
