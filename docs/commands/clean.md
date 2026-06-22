# clean

清理并格式化项目代码。默认工具链为 `autoflake` 与 `black`，可在 `.autoship.toml` 的 `[clean]` 段中自定义。

## 语法

```bash
autoship clean [OPTIONS] [PATHS]...
```

## 参数

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `paths` | 否 | 要清理的路径，默认为当前目录（动态检测） |

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--check` | `False` | 若需要修改则返回非零退出码 |
| `-y` | `--yes` | `False` | 跳过交互式确认 |

## 示例

清理当前目录：

```bash
autoship clean
```

指定路径：

```bash
autoship clean src tests
```

CI 场景下检查是否需要格式化：

```bash
autoship clean --check
```

跳过确认：

```bash
autoship clean --yes
```

预期输出示例：

```text
reformatted /path/to/project/hello.py

All done! ✨ 🍰 ✨
1 file reformatted.
Clean complete.
```

## 输出说明 / 常见错误

- `--check` 模式下如果文件需要修改，命令会返回非零退出码，适合在 CI 中使用。
- 若缺少配置的清理工具，会提示安装建议。

## 相关命令

- [verify](./verify.md) — 运行验证
- [commit](./commit.md) — 提交改动
