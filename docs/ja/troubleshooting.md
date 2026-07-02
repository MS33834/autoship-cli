---
title: トラブルシューティング
---
# トラブルシューティング

> 本ページでは AutoShip のよくある不具合と診断手順をまとめます。まず `autoship doctor` で自己診断し、以下の該当項目を確認してください。コマンドコードブロックは英語のまま維持します。

## インストール失敗

### `autoship` コマンドが見つからない（PATH 問題）

```bash
pipx list
pipx ensurepath
```

`pipx ensurepath` は pipx の bin ディレクトリを PATH に書き込みます。実行後、**ターミナルを開き直す**かシェル設定（`~/.bashrc` / `~/.zshrc`）を `source` して再試行してください。

### pipx とシステム pip の衝突

以前 `pip install autoship` で旧版を入れていると、旧パスが優先されることがあります：

```bash
pip uninstall autoship
pipx install autoship
which -a autoship
```

### 権限不足 / EACCES

`sudo pip install` は避けてください。推奨：

```bash
pipx install autoship
# または
uv tool install autoship
```

pip を使う必要がある場合は、`python -m site --user-base` が示すユーザーディレクトリに書き込み権があるか先に確認してください。

## `init` がハングする

### 対話式アンケートで止まる

`init` は既定でいくつか質問します。CI やスクリプト環境では `--yes` でスキップ：

```bash
autoship init --yes
```

### 「モデルバックエンド検出」で止まる

`init` はローカルの Ollama / LM Studio を検出しようとします。バックエンド未起動だとタイムアウト待ちになります。対応：

- Ollama を起動して再試行；
- または `--no-model` で検出をスキップし、後で `.autoship.toml` に設定。

## `clean` の誤削除を復元する

`clean` は不要な import 削除 / コード並び替えの前に、Git ステージング前のバックアップを取ります。誤削除に気付いた場合：

```bash
# 変更を確認
git diff

# clean の変更を破棄し HEAD に戻す
git checkout -- .

# 既にコミット済みなら1回戻す
git reset --hard HEAD~1
```

> 推奨：`clean` 前に `git status` で作業ツリーがクリーンか確認するか、`--dry-run` でプレビューしてください。

## `commit` の空メッセージ / タイムアウト

### 生成されたコミットメッセージが空

- ステージ済みの変更があるか確認：`git diff --cached`。
- AI バックエンド使用時はバックエンドが利用可能か確認（下記参照）。
- 一時的にテンプレートモードに退避：

```bash
autoship commit --no-ai
```

### AI 生成がタイムアウト

モデルが大きすぎるかバックエンド応答が遅いとタイムアウトします。`.autoship.toml` で調整：

```toml
[commit]
timeout_seconds = 60
```

またはより小さなローカルモデルに切り替えてください。

## `verify --fix` がバックエンドに接続できない

`verify --fix` には利用可能な AI バックエンドが必須です。ない場合は「no AI backend configured」と報告されます。

```bash
# 1. バックエンド状態を確認
autoship doctor

# 2. Ollama が起動しているか確認
ollama list

# 3. verbose で詳細エラーを確認
autoship --verbose verify --fix pytest
```

詳しくは [既知の問題](known-issues.md) の「`verify --fix` は AI バックエンドがないと利用不可」を参照。

## `upload` の認証エラー

### PyPI トークンが無効 / 403

- トークンが **API Token**（ユーザー名/パスワードではない）で、scope が対象プロジェクトを含むか確認。
- 設定ファイルへの書き込みを避け、環境変数で注入：

```bash
export TWINE_PASSWORD=pypi-xxxxxxxx
autoship upload --target pypi
```

### Docker Registry 401

```bash
docker login ghcr.io
# または
docker login registry.hub.docker.com
```

`upload --target docker` はローカルで `docker login` 済みであることに依存します。

## 三言語切り替えが効かない

### `--lang` が無効

```bash
autoship --lang en <command>
```

出力が依然として中国語の場合は以下を確認：

1. `.autoship.toml` で `locale` が設定されていないか——設定は CLI フラグ以外の方法より優先されます；
2. インストールしたバージョンがその言語をサポートしているか（`autoship --version` を実行しリリースノートと照合）；
3. ドキュメントサイトの言語切り替えは i18n プラグインがルーティングし、CLI 出力言語とは独立しています。

詳しくは [よくある質問](faq.md) の「言語を切り替えるには？」を参照。

## それでも解決しない場合

- `autoship doctor` を実行し出力を添える；
- [既知の問題](known-issues.md) を確認；
- issue を作成：[GitHub Issues](https://github.com/MS33834/autoship-cli/issues)。
