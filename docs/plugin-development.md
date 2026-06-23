# 插件开发指南

AutoShip-CLI 的插件系统基于 [pluggy](https://pluggy.readthedocs.io/)。你只需实现 `autoship.hookspec.AutoShipHookSpec` 中定义的钩子，并将插件对象注册到 `autoship.plugins` entry point。

> 推荐使用 [`autoship-sdk`](https://pypi.org/project/autoship-sdk/) 简化插件开发，
> 它提供了基类、装饰器和测试工具。

## 使用 autoship-sdk（推荐）

安装 SDK：

```bash
pip install autoship-sdk
```

最小插件示例：

```python
from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class MyPlugin(Plugin):
    @hook
    def pre_commit(self, context: CommandContext) -> None:
        print(f"About to commit in {context.project_root}")
```

通过 `pyproject.toml` 注册：

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin.plugin:MyPlugin"
```

### 测试插件

`PluginTestHarness` 提供隔离的 Hook 调用环境：

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

### 项目脚手架

```python
from autoship_sdk import create_plugin
from pathlib import Path

create_plugin(
    target_dir=Path("./autoship-my-plugin"),
    plugin_name="my-plugin",
    description="My first AutoShip plugin",
)
```

这会生成包含 `pyproject.toml`、`README.md`、插件源码和测试结构的完整项目。

## CommandContext

所有钩子都接收一个不可变的 `CommandContext`：

```python
@dataclass(frozen=True)
class CommandContext:
    command: str              # 当前命令名，如 "verify"
    project_root: Path        # 项目根目录
    config: AppConfig         # 加载后的配置对象
    verbose: bool = False     # 是否开启详细输出
    dry_run: bool = False     # 是否仅预览
    yes: bool = False         # 是否跳过确认
    trace_id: str = ""        # 审计追踪 ID
    extras: dict[str, Any] = field(default_factory=dict)  # 命令额外参数
```

命令可以通过 `extras` 向钩子传递额外信息。例如 `verify` 命令会传入 `{"verify_command": ..., "fix": ...}`。

## 最小插件示例

创建 `my_plugin.py`：

```python
from autoship.core.context import CommandContext
from autoship.hookspec import hookimpl


class MyPlugin:
    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        print(f"About to commit in {context.project_root}")


plugin = MyPlugin()
```

## 通过 entry_points 注册

推荐将插件打包为独立 Python 包，并通过 `pyproject.toml` 注册：

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin:plugin"
```

其中 `my_plugin:plugin` 指向包含钩子方法的插件对象。也可以指向一个返回插件对象的工厂函数：

```toml
[project.entry-points."autoship.plugins"]
my_plugin = "my_plugin.plugin:register"
```

```python
def register():
    return MyPlugin()
```

AutoShip 启动时会自动发现并加载所有 `autoship.plugins` entry points。

## 完整示例：on_error 修复建议

以下插件在 `verify --fix` 失败时返回一个修复建议：

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

## 安装与验证

1. 安装插件包：

```bash
pip install -e .
```

2. 检查插件是否被加载：

```bash
autoship --verbose verify pytest
```

3. 运行单元测试（参考本仓库 `examples/custom-plugin`）。

## 仓库示例

参见 [`examples/custom-plugin`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin)。该示例实现：

- `pre_commit`：在提交前扫描项目根目录下的 `TODO` 文件并告警。
- `on_error`：当 `verify` 失败且用户启用 `--fix` 时，返回一条 `FixSuggestion`。

## 最佳实践

- **只捕获你关心的异常**：`on_error` 中不要吞掉关键异常，返回 `None` 让其他插件处理。
- **避免副作用**：`pre_*` / `post_*` 钩子应轻量，复杂操作建议异步或子进程执行。
- **尊重 `dry_run` 与 `yes`**：在修改文件系统或远程状态前检查这两个标志。
- **不要泄露敏感信息**：从 `context.config` 读取凭证时避免打印到日志。
- **使用类型注解**：便于静态检查（pyright / mypy）并保持与核心代码一致。

## 完整示例：自定义验证插件

下面以“提交前敏感文件检查插件”为例，演示如何从 0 到 1 开发、测试并安装一个 AutoShip 插件。该插件使用 `autoship-sdk`，在 `pre_commit` 阶段扫描项目根目录，若发现 `.env`、`secrets.json` 等敏感文件存在，则阻止提交并给出明确提示。

### 项目结构

```text
autoship-no-secret-plugin/
├── pyproject.toml
├── README.md
└── src/
    └── autoship_no_secret_plugin/
        ├── __init__.py
        └── plugin.py
```

建议使用 `src` 布局，避免运行时意外导入源码目录，也便于打包工具（hatchling、setuptools 等）正确解析包路径。

### pyproject.toml 配置

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

说明：

- `[build-system]` 使用 `hatchling`，轻量且无需额外 `MANIFEST.in`。
- `[project.entry-points."autoship.plugins"]` 将插件注册到 AutoShip 的插件命名空间；`no_secret` 是插件 ID，`autoship_no_secret_plugin.plugin:register` 指向工厂函数。
- 依赖中同时声明 `autoship` 与 `autoship-sdk`，前者用于类型与运行时兼容，后者提供 `Plugin` 基类与 `hook` 装饰器。

### 插件代码

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
        # 在 dry-run 模式下只做提示，不阻塞实际工作流
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

要点：

- 继承 `autoship_sdk.Plugin` 并使用 `@hook` 注册钩子，比直接操作 `hookimpl` 更简洁。
- 通过 `context.project_root` 定位文件，而不是 `Path.cwd()`，确保在子目录执行 `autoship commit` 时也能正确检查。
- 检查 `context.dry_run`，避免在预览模式下抛出异常；对于阻塞类检查，dry-run 通常应静默跳过。
- 使用具体异常类型（如 `RuntimeError`）而非 `SystemExit`，让 AutoShip 的错误处理与审计日志能捕获并展示。

### 测试示例

在插件目录下新建 `tests/test_plugin.py`：

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

    # PluginTestHarness 提供的 project_root 是一个临时目录
    secret = ctx.project_root / ".env"
    secret.write_text("SECRET=1\n")

    with pytest.raises(RuntimeError, match=".env"):
        harness.call("pre_commit", ctx)
```

测试策略：

- 正向用例确认没有敏感文件时插件不报错。
- 负向用例在 `project_root` 临时目录中写入 `.env`，验证插件会抛出包含文件名的异常。
- 使用 `PluginTestHarness` 隔离 Hook 调用环境，避免影响真实项目。

运行测试：

```bash
cd autoship-no-secret-plugin
pytest
```

### 安装与验证

1. 以可编辑模式安装插件：

    ```bash
    cd autoship-no-secret-plugin
    pip install -e .
    ```

2. 检查 AutoShip 是否已加载该插件：

    ```bash
    autoship --verbose plugin list
    ```

    应看到类似输出：

    ```text
    Name              Version    Trust        Source
    ----------------- ---------- ------------ -------------------------------
    builtin           0.2.0      builtin      autoship.builtin
    no_secret         0.1.0      community    autoship_no_secret_plugin
    ```

3. 在任意项目中测试 dry-run 模式：

    ```bash
    autoship commit --dry-run
    ```

    由于插件在 `dry_run` 下直接返回，不会阻塞。

4. 触发真实拦截：

    ```bash
    touch .env
    autoship commit
    ```

    预期 AutoShip 在 `pre_commit` 阶段捕获异常并提示：

    ```text
    [no-secret-plugin] Blocked commit: sensitive file '.env' exists.
    Add it to .gitignore or remove it.
    ```

5. 清理后再次提交：

    ```bash
    rm .env
    autoship commit
    ```

### 与本仓库示例的关系

本仓库的 [`examples/custom-plugin/`](../examples/custom-plugin/) 同样实现了 `pre_commit`（检查 `TODO` 文件）与 `on_error`（返回 `FixSuggestion`）。两者的区别仅在于业务逻辑：

- `custom-plugin` 适合学习如何在失败时给出修复建议。
- 本节的 `no-secret-plugin` 适合学习如何进行轻量级前置检查，并尊重 `dry_run`、使用具体异常、保持项目路径无关。

开发插件时，建议优先使用 `autoship-sdk` 的 `Plugin` + `@hook` 模式；如果只需要一个简单函数式插件，再考虑直接使用 `hookimpl`。
