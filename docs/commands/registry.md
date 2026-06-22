# registry

查看插件注册表分析与同步远程索引。

## 语法

```bash
autoship registry [OPTIONS] COMMAND [ARGS]...
```

## 参数

`registry` 命令本身不接受位置参数，需通过子命令操作。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | 显示帮助信息并退出 |

## 子命令

### registry list

显示注册表分析面板。

```bash
autoship registry list [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--top INTEGER` | `5` | 排行榜中显示的插件数量 |

### registry dashboard

显示注册表分析面板（与 `list` 行为一致）。

```bash
autoship registry dashboard [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--top INTEGER` | `5` | 排行榜中显示的插件数量 |

### registry sync

从远程源同步插件注册表索引。

```bash
autoship registry sync [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| `-o` | `--output PATH` | `~/.autoship/registry/plugins.json` | 同步后的注册表索引输出路径 |
| `-f` | `--force` | `False` | 强制覆盖本地缓存 |
| - | `--dry-run` | `False` | 显示变更但不写入 |

## 示例

查看注册表分析面板：

```bash
autoship registry list
```

显示前 10 个插件：

```bash
autoship registry list --top 10
```

同步远程注册表索引：

```bash
autoship registry sync
```

强制覆盖本地缓存：

```bash
autoship registry sync --force
```

预览同步变更：

```bash
autoship registry sync --dry-run
```

## 输出说明 / 常见错误

- `list` 与 `dashboard` 当前显示相同内容。
- 同步默认写入 `~/.autoship/registry/plugins.json`，请确保目录可写。
- 网络不可用时 `sync` 会失败，可先检查 `doctor` 网络诊断。

## 相关命令

- [plugin](./plugin.md) — 安装、卸载和管理插件
- [doctor](./doctor.md) — 检查环境与网络
