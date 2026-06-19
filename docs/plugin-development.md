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

参见 [`examples/custom-plugin`](https://github.com/autoship-cli/autoship-cli/tree/main/examples/custom-plugin)。该示例实现：

- `pre_commit`：在提交前扫描项目根目录下的 `TODO` 文件并告警。
- `on_error`：当 `verify` 失败且用户启用 `--fix` 时，返回一条 `FixSuggestion`。

## 最佳实践

- **只捕获你关心的异常**：`on_error` 中不要吞掉关键异常，返回 `None` 让其他插件处理。
- **避免副作用**：`pre_*` / `post_*` 钩子应轻量，复杂操作建议异步或子进程执行。
- **尊重 `dry_run` 与 `yes`**：在修改文件系统或远程状态前检查这两个标志。
- **不要泄露敏感信息**：从 `context.config` 读取凭证时避免打印到日志。
- **使用类型注解**：便于静态检查（pyright / mypy）并保持与核心代码一致。
