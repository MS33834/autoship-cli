# 命令参考

AutoShip CLI 的命令遵循统一的生命周期：读取配置、调用 `pre_*` Hook、执行主体、调用 `post_*` Hook、记录审计日志。

## 全局选项

```text
-v, --verbose      详细输出
-n, --dry-run      仅预览，不执行
-y, --yes          跳过确认
-c, --config PATH  指定配置文件路径
```

## `autoship init`

初始化项目配置，生成 `.autoship.toml`。

```bash
autoship init
autoship init --type python
autoship init -o autoship.toml
```

| 选项 | 说明 |
|---|---|
| `--type TEXT` | 强制指定项目类型 |
| `-o, --output PATH` | 配置文件输出路径，默认为 `.autoship.toml` |

执行时会自动检测项目类型与硬件能力，并推荐合适的模型层级。

## `autoship clean`

运行代码清理与格式化工具链。

```bash
autoship clean
autoship clean src tests
autoship clean --check
```

| 选项 | 说明 |
|---|---|
| `paths` | 要清理的路径，默认为当前目录 |
| `--check` | 若需要修改则返回非零退出码 |

默认工具链为 `autoflake` 与 `black`，可在配置文件中自定义。

## `autoship commit`

生成提交信息并执行 Git 提交。

```bash
autoship commit
autoship commit -m "fix: resolve upload timeout"
autoship commit --no-edit
```

| 选项 | 说明 |
|---|---|
| `-m, --message TEXT` | 直接使用给定的提交信息 |
| `--edit / --no-edit` | 是否打开编辑器审阅生成的信息，默认开启 |

当没有提供 `-m` 时，AutoShip 会调用本地模型根据 diff 与 stats 生成 Conventional Commits 风格的提交信息。

## `autoship verify`

运行验证命令，并在失败时支持 AI 辅助修复。

```bash
autoship verify pytest
autoship verify "pytest tests/unit"
autoship verify pytest --fix
```

| 参数 | 说明 |
|---|---|
| `command` | 要运行的验证命令，如 `pytest`、`mypy src` |

| 选项 | 说明 |
|---|---|
| `--fix` | 失败时调用模型生成修复建议 |

`--fix` 会触发插件的 `on_error` Hook，收集 `FixSuggestion` 并提示用户应用补丁。

## `autoship upload`

上传产物到指定目标。

```bash
autoship upload --target pypi
autoship upload --target docker --image myapp --tag 0.1.0
autoship upload --target github --tag v0.1.0 --artifact dist/*.whl
```

| 选项 | 说明 |
|---|---|
| `--target TEXT` | 上传目标：`pypi`、`docker`、`github` |
| `--image TEXT` | Docker 镜像名称 |
| `-t, --tag TEXT` | Docker 镜像标签或 GitHub release 标签 |
| `--artifact TEXT` | 要上传的产物，可多次指定 |

## `autoship plugin`

管理插件。

```bash
# 列出已注册插件
autoship plugin list

# 安装插件
autoship plugin install my-plugin
autoship plugin install ./local-plugin --trust verified

# 调整信任等级
autoship plugin trust my-plugin verified

# 卸载插件
autoship plugin uninstall my-plugin
```

| 子命令 | 说明 |
|---|---|
| `list` | 列出所有已注册插件 |
| `install SOURCE` | 安装插件包并注册 |
| `uninstall NAME` | 卸载插件包并移除注册 |
| `trust NAME LEVEL` | 修改插件信任等级 |

信任等级：`builtin`、`verified`、`community`、`untrusted`。

## `autoship doctor`

诊断当前环境是否满足 AutoShip 运行要求。

```bash
autoship doctor
autoship doctor --json
```

| 选项 | 说明 |
|---|---|
| `--json` | 以 JSON 格式输出诊断报告 |

检查项包括：Python 版本、Git 配置、模型后端连通性、clean 工具链、
插件外部依赖、审计/遥测目录权限等。输出分级为 OK / WARNING / ERROR。

## `autoship audit`

导出或清理审计日志。

```bash
# 导出最近 30 天的审计记录
autoship audit export --since 30d

# 导出到指定文件
autoship audit export --since 2025-01-01 --output ./audit.jsonl

# 清理 90 天前的日志
autoship audit cleanup --retention 90
```

| 子命令 | 说明 |
|---|---|
| `export` | 将审计记录导出为 JSON Lines 文件 |
| `cleanup` | 删除超过保留期的审计日志 |

`export` 的 `--since` 支持 ISO 日期或相对天数（如 `1d`、`7d`、`30d`）。
审计日志默认存放在项目根目录的 `.autoship/audit/` 下，可通过配置或
环境变量调整。
