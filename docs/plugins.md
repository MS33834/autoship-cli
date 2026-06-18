# AutoShip-CLI 插件开发指南

AutoShip-CLI 采用 [pluggy](https://pluggy.readthedocs.io/) 实现插件化架构。插件通过声明生命周期钩子（Hooks）来扩展命令行为，例如在执行 `verify` 前做额外检查，或在命令失败时给出 AI 修复建议。

## 目录

- [可用钩子](#可用钩子)
- [CommandContext](#commandcontext)
- [最小插件示例](#最小插件示例)
- [通过 entry_points 注册](#通过-entry_points-注册)
- [安装与验证](#安装与验证)
- [完整示例](#完整示例)
- [最佳实践](#最佳实践)

## 可用钩子

所有钩子定义在 `autoship.hookspec.AutoShipHookSpec` 中：

| 钩子名 | 触发时机 | 返回值 |
|---|---|---|
| `pre_init` | `autoship init` 写入配置文件之前 | `None` |
| `post_init` | `autoship init` 写入配置文件之后 | `None` |
| `pre_clean` | `autoship clean` 运行清理工具之前 | `None` |
| `post_clean` | `autoship clean` 运行清理工具之后 | `None` |
| `pre_commit` | `autoship commit` 生成提交信息之前 | `None` |
| `post_commit` | `autoship commit` 完成之后 | `None` |
| `pre_verify` | `autoship verify` 运行验证命令之前 | `None` |
| `post_verify` | `autoship verify` 完成之后 | `None` |
| `pre_upload` | `autoship upload` 发布产物之前 | `None` |
| `post_upload` | `autoship upload` 完成之后 | `None` |
| `on_error` | 命令执行抛出异常时 | `FixSuggestion \| None` |

`on_error` 是唯一允许返回值的钩子。当命令带 `--fix` 标志失败时，AutoShip 会收集所有 `FixSuggestion`，展示给用户并可选地应用补丁。

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

## 完整示例

参见 [`examples/custom-plugin`](../examples/custom-plugin)。该示例实现：

- `pre_commit`：在提交前扫描项目根目录下的 `TODO` 文件并告警。
- `on_error`：当 `verify` 失败且用户启用 `--fix` 时，返回一条 `FixSuggestion`。

## 最佳实践

- **只捕获你关心的异常**：`on_error` 中不要吞掉关键异常，返回 `None` 让其他插件处理。
- **避免副作用**：`pre_*` / `post_*` 钩子应轻量，复杂操作建议异步或子进程执行。
- **尊重 `dry_run` 与 `yes`**：在修改文件系统或远程状态前检查这两个标志。
- **不要泄露敏感信息**：从 `context.config` 读取凭证时避免打印到日志。
- **使用类型注解**：便于静态检查（pyright / mypy）并保持与核心代码一致。
