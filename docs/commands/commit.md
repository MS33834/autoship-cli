# commit

生成提交信息并执行 Git 提交。当未提供 `-m` 时，AutoShip 会调用本地模型根据 diff 与 stats 生成 Conventional Commits 风格的提交信息。

## 语法

```bash
autoship commit [OPTIONS]
```

## 参数

`commit` 命令不接受位置参数。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| `-m` | `--message TEXT` | - | 直接使用给定的提交信息 |
| - | `--edit / --no-edit` | `edit` | 是否打开编辑器审阅生成的信息 |

## 示例

暂存改动后生成提交信息：

```bash
autoship commit
```

直接指定提交信息：

```bash
autoship commit -m "fix: resolve upload timeout"
```

跳过编辑器确认：

```bash
autoship commit --no-edit
```

## 输出说明 / 常见错误

- 使用 `-m` 时不会调用 AI，直接以给定消息提交。
- 未配置模型时会提示手动编辑提交信息。
- 提交前会运行 `pre_commit` Hook，可在插件中扩展。

## 相关命令

- [clean](./clean.md) — 清理代码
- [verify](./verify.md) — 验证改动
- [upload](./upload.md) — 提交后上传产物
