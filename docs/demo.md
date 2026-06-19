# AutoShip-CLI 文字版演示

下面展示一个典型的本地 Python 项目交付流程：初始化、清理、验证、提交与上传产物。

## 环境准备

假设你已经在虚拟环境中安装好了 AutoShip：

```bash
pipx install autoship
# 或：pip install autoship
```

## 1. 初始化项目

在项目根目录执行：

```bash
$ autoship init
```

预期输出：

```text
Detected project type: python
Recommended model tier: local (ollama/llama3.2)
Created config: .autoship.toml
```

生成的 `.autoship.toml` 类似：

```toml
[project]
name = "my-app"
type = "python"

[clean]
toolchain = ["autoflake", "black"]

[verify]
default = "pytest"

[upload]
targets = ["pypi"]
```

## 2. 清理与格式化

运行代码清理工具链：

```bash
$ autoship clean
```

预期输出：

```text
Running clean toolchain: autoflake, black
 autoflake --remove-all-unused-imports --recursive src tests
 black src tests
All files left unchanged.
```

如果文件需要修改，输出会列出被格式化的文件路径。加 `--check` 可在需要修改时返回非零退出码，适合 CI：

```bash
$ autoship clean --check
```

## 3. 运行验证

以 `pytest` 为例：

```bash
$ autoship verify pytest
```

预期输出：

```text
Running: pytest
============================= test session starts ==============================
platform linux -- Python 3.12.0, pytest-8.3.0, pluggy-1.5.0
rootdir: /home/user/my-app
collected 12 items

tests/unit/test_core.py ......                                        [ 50%]
tests/unit/test_plugins.py ......                                     [100%]

============================== 12 passed in 0.42s ==============================
```

如果验证失败且你启用了 `--fix`，AutoShip 会调用插件的 `on_error` Hook 并提示可选修复：

```bash
$ autoship verify pytest --fix
```

## 4. 生成并提交

让 AutoShip 根据 diff 自动生成 Conventional Commits 风格的提交信息：

```bash
$ autoship commit
```

预期输出：

```text
Generating commit message (local model)...

feat(core): add plugin verification lifecycle

- Introduce pre_verify / post_verify hooks
- Add FixSuggestion dataclass for error recovery

Apply this message? [Y/n/e(edit)]
```

确认后完成 Git 提交：

```text
[main 3a9f2c1] feat(core): add plugin verification lifecycle
 3 files changed, 120 insertions(+)
```

也可以直接指定提交信息，跳过生成：

```bash
$ autoship commit -m "fix: resolve upload timeout"
```

## 5. 上传产物

打包并上传到 PyPI：

```bash
$ autoship upload --target pypi
```

预期输出：

```text
Building wheel and sdist...
  my-app-0.1.0-py3-none-any.whl
  my-app-0.1.0.tar.gz
Uploading distributions to https://upload.pypi.org/legacy/
Upload successful: my-app 0.1.0
```

上传 Docker 镜像的示例：

```bash
$ autoship upload --target docker --image myapp --tag 0.1.0
```

## 6. 查看已加载的插件

```bash
$ autoship plugin list
```

预期输出：

```text
Name              Version    Trust        Source
----------------- ---------- ------------ ------------------------
builtin           0.2.0      builtin      autoship.builtin
autoship_custom   0.1.0      community    autoship_custom_plugin
```

## 更多命令

- `autoship doctor`：一键诊断环境。
- `autoship audit export --since 7d`：导出最近 7 天审计日志。
- `autoship --help`：查看所有子命令与全局选项。

完整命令参考请见 [docs/commands.md](./commands.md)。
