# プラグイン開発ガイド

AutoShip-CLI のプラグインシステムは [pluggy](https://pluggy.readthedocs.io/) に基づいています。`autoship.hookspec.AutoShipHookSpec` で定義されたフックを実装し、プラグインオブジェクトを `autoship.plugins` entry point に登録するだけです。

> [`autoship-sdk`](https://pypi.org/project/autoship-sdk/) を使用してプラグイン開発を簡素化することを推奨します。
> ベースクラス、デコレータ、テストツールが提供されています。

## autoship-sdk の使用（推奨）

SDK をインストール：

```bash
pip install autoship-sdk
```

最小プラグインの例：

```python
from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class MyPlugin(Plugin):
    @hook
    def pre_commit(self, context: CommandContext) -> None:
        print(f"About to commit in {context.project_root}")
```

`pyproject.toml` で登録：

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin.plugin:MyPlugin"
```

### プラグインのテスト

`PluginTestHarness` は分離された Hook 呼び出し環境を提供します：

```python
from autoship_sdk.testing import PluginTestHarness
from my_plugin.plugin import MyPlugin


def test_pre_commit():
    harness = PluginTestHarness()
    harness.register(MyPlugin())
    ctx = harness.make_context("commit")
    results = harness.call("pre_commit", ctx)
    assert results == [None]
```

### プロジェクトスキャフォールド

```python
from autoship_sdk import create_plugin
from pathlib import Path

create_plugin(
    target_dir=Path("./autoship-my-plugin"),
    plugin_name="my-plugin",
    description="My first AutoShip plugin",
)
```

これにより `pyproject.toml`、`README.md`、プラグインのソースコード、テスト構造を含む完全なプロジェクトが生成されます。

## CommandContext

すべてのフックは不変の `CommandContext` を受け取ります：

```python
@dataclass(frozen=True)
class CommandContext:
    command: str              # 現在のコマンド名（例："verify"）
    project_root: Path        # プロジェクトルートディレクトリ
    config: AppConfig         # 読み込み済みの設定オブジェクト
    verbose: bool = False     # 詳細出力が有効かどうか
    dry_run: bool = False     # プレビューのみかどうか
    yes: bool = False         # 確認をスキップするかどうか
    trace_id: str = ""        # 監査トレース ID
    extras: dict[str, Any] = field(default_factory=dict)  # コマンドの追加パラメータ
```

コマンドは `extras` を通じてフックに追加情報を渡すことができます。例えば `verify` コマンドは `{"verify_command": ..., "fix": ...}` を渡します。

## 最小プラグインの例

`my_plugin.py` を作成：

```python
from autoship.core.context import CommandContext
from autoship.hookspec import hookimpl


class MyPlugin:
    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        print(f"About to commit in {context.project_root}")


plugin = MyPlugin()
```

## entry_points での登録

プラグインを独立した Python パッケージとしてパッケージ化し、`pyproject.toml` で登録することを推奨します：

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin:plugin"
```

`my_plugin:plugin` はフックメソッドを含むプラグインオブジェクトを指します。プラグインオブジェクトを返すファクトリ関数を指すこともできます：

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin.plugin:register"
```

```python
def register():
    return MyPlugin()
```

AutoShip は起動時にすべての `autoship.plugins` entry points を自動的に発見して読み込みます。

## 完全な例：on_error 修正提案

以下のプラグインは `verify --fix` の失敗時に修正提案を返します：

```python
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.hookspec import hookimpl


class FixOnVerifyPlugin:
    @hookimpl
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        if context.command != "verify":
            return None

        message = str(error)
        if "ImportError" not in message:
            return None

        return FixSuggestion(
            description="Missing dependency detected; run `uv pip install -e .`",
            patch="",
        )


plugin = FixOnVerifyPlugin()
```

## インストールと検証

1. プラグインパッケージをインストール：

```bash
pip install -e .
```

2. プラグインが読み込まれているか確認：

```bash
autoship --verbose verify pytest
```

3. ユニットテストを実行（本リポジトリの `examples/custom-plugin` を参照）。

## リポジトリの例

[`examples/custom-plugin`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin) を参照してください。この例は以下を実装しています：

- `pre_commit`：コミット前にプロジェクトルートディレクトリの `TODO` ファイルをスキャンして警告。
- `on_error`：`verify` が失敗しユーザーが `--fix` を有効にした場合、`FixSuggestion` を返す。

## ベストプラクティス

- **関心のある例外のみキャッチ**：`on_error` で重要な例外を飲み込まないでください。`None` を返して他のプラグインに処理を委ねます。
- **副作用を避ける**：`pre_*` / `post_*` フックは軽量にし、複雑な操作は非同期またはサブプロセスでの実行を推奨します。
- **`dry_run` と `yes` を尊重**：ファイルシステムやリモート状態を変更する前にこれらのフラグを確認してください。
- **機密情報を漏洩しない**：`context.config` から資格情報を読み取る際、ログへの出力を避けてください。
- **型アノテーションを使用**：静的チェック（pyright / mypy）がしやすく、コアコードとの一貫性が保たれます。

## 完全な例：カスタム検証プラグイン

以下に「コミット前の機密ファイルチェックプラグイン」を例として、AutoShip プラグインをゼロから開発、テスト、インストールする方法を示します。このプラグインは `autoship-sdk` を使用し、`pre_commit` フェーズでプロジェクトルートディレクトリをスキャンし、`.env`、`secrets.json` などの機密ファイルが存在する場合はコミットをブロックして明確なメッセージを表示します。

### プロジェクト構成

```text
autoship-no-secret-plugin/
├── pyproject.toml
├── README.md
└── src/
    └── autoship_no_secret_plugin/
        ├── __init__.py
        └── plugin.py
```

`src` レイアウトの使用を推奨します。実行時にソースコードディレクトリが誤ってインポートされるのを防ぎ、パッケージツール（hatchling、setuptools など）がパッケージパスを正しく解決できます。

### pyproject.toml の設定

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "autoship-no-secret-plugin"
version = "0.1.0"
description = "Block commits when common secret files are present"
requires-python = ">=3.10"
dependencies = [
    "autoship>=0.2.0b1",
    "autoship-sdk>=0.1.0b1",
]

[project.entry-points."autoship.plugins"]
no_secret = "autoship_no_secret_plugin.plugin:register"
```

説明：

- `[build-system]` は `hatchling` を使用します。軽量で追加の `MANIFEST.in` が不要です。
- `[project.entry-points."autoship.plugins"]` はプラグインを AutoShip のプラグイン名前空間に登録します。`no_secret` はプラグイン ID、`autoship_no_secret_plugin.plugin:register` はファクトリ関数を指します。
- 依存関係に `autoship` と `autoship-sdk` の両方を宣言します。前者は型とランタイムの互換性に、後者は `Plugin` ベースクラスと `hook` デコレータに使用します。

### プラグインコード

`src/autoship_no_secret_plugin/__init__.py`：

```python
"""AutoShip plugin that prevents accidental commits of secret files."""
```

`src/autoship_no_secret_plugin/plugin.py`：

```python
from __future__ import annotations

from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class NoSecretPlugin(Plugin):
    """Scan the project root for sensitive files before each commit."""

    SENSITIVE_PATTERNS = (".env", "secrets.json", "credentials.json")

    @hook
    def pre_commit(self, context: CommandContext) -> None:
        """Raise an error if a sensitive file is found in the project root."""
        # dry-run モードでは警告のみで、実際のワークフローはブロックしない
        if context.dry_run:
            return

        for name in self.SENSITIVE_PATTERNS:
            path = context.project_root / name
            if path.exists():
                raise RuntimeError(
                    f"[no-secret-plugin] Blocked commit: sensitive file "
                    f"'{path.name}' exists. Add it to .gitignore or remove it."
                )


def register() -> NoSecretPlugin:
    """Factory used by the ``autoship.plugins`` entry point."""
    return NoSecretPlugin()
```

ポイント：

- `autoship_sdk.Plugin` を継承し `@hook` でフックを登録する方が、`hookimpl` を直接操作するよりも簡潔です。
- `Path.cwd()` ではなく `context.project_root` でファイルを特定することで、サブディレクトリで `autoship commit` を実行した場合でも正しくチェックできます。
- `context.dry_run` をチェックし、プレビューモードでは例外をスローしないようにします。ブロッキング系のチェックでは dry-run は通常サイレントにスキップすべきです。
- `SystemExit` ではなく具体的な例外型（`RuntimeError` など）を使用し、AutoShip のエラー処理と監査ログでキャプチャして表示できるようにします。

### テスト例

プラグインディレクトリに `tests/test_plugin.py` を作成：

```python
import pytest
from autoship_sdk.testing import PluginTestHarness

from autoship_no_secret_plugin.plugin import NoSecretPlugin


def test_pre_commit_allows_clean_project():
    harness = PluginTestHarness()
    harness.register(NoSecretPlugin())
    ctx = harness.make_context("commit")
    results = harness.call("pre_commit", ctx)
    assert results == [None]


def test_pre_commit_blocks_secret_file():
    harness = PluginTestHarness()
    harness.register(NoSecretPlugin())
    ctx = harness.make_context("commit")

    # PluginTestHarness の project_root は一時ディレクトリ
    secret = ctx.project_root / ".env"
    secret.write_text("SECRET=1\n")

    with pytest.raises(RuntimeError, match=".env"):
        harness.call("pre_commit", ctx)
```

テスト戦略：

- 正方向のユースケースで機密ファイルがない場合にプラグインがエラーを出さないことを確認。
- 負方向のユースケースで `project_root` の一時ディレクトリに `.env` を書き込み、プラグインがファイル名を含む例外をスローすることを検証。
- `PluginTestHarness` を使用して Hook 呼び出し環境を分離し、実際のプロジェクトへの影響を回避。

テストの実行：

```bash
cd autoship-no-secret-plugin
pytest
```

### インストールと検証

1. 編集可能モードでプラグインをインストール：

    ```bash
    cd autoship-no-secret-plugin
    pip install -e .
    ```

2. AutoShip がプラグインを読み込んだか確認：

    ```bash
    autoship --verbose plugin list
    ```

    以下のような出力が表示されるはずです：

    ```text
    Name              Version    Trust        Source
    ----------------- ---------- ------------ -------------------------------
    builtin           0.2.0      builtin      autoship.builtin
    no_secret         0.1.0      community    autoship_no_secret_plugin
    ```

3. 任意のプロジェクトで dry-run モードをテスト：

    ```bash
    autoship commit --dry-run
    ```

    プラグインは `dry_run` の場合は直接 return するため、ブロックされません。

4. 実際のブロックをトリガー：

    ```bash
    touch .env
    autoship commit
    ```

    AutoShip が `pre_commit` フェーズで例外をキャプチャし、以下を表示することが期待されます：

    ```text
    [no-secret-plugin] Blocked commit: sensitive file '.env' exists.
    Add it to .gitignore or remove it.
    ```

5. クリーンアップ後に再度コミット：

    ```bash
    rm .env
    autoship commit
    ```

### 本リポジトリの例との関係

本リポジトリの [`examples/custom-plugin/`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin) も `pre_commit`（`TODO` ファイルのチェック）と `on_error`（`FixSuggestion` の返却）を実装しています。両者の違いはビジネスロジックのみです：

- `custom-plugin` は失敗時に修正提案を出す方法を学ぶのに適しています。
- この節の `no-secret-plugin` は軽量な事前チェックを行い、`dry_run` を尊重し、具体的な例外を使用し、プロジェクトパスに依存しない方法を学ぶのに適しています。

プラグイン開発時は、まず `autoship-sdk` の `Plugin` + `@hook` パターンを使用することを推奨します。シンプルな関数型プラグインが必要な場合のみ、`hookimpl` の直接使用を検討してください。
