# metrics

查看运行时指标，支持显示和导出为 JSON。

## 语法

```bash
autoship metrics [OPTIONS] COMMAND [ARGS]...
```

## 参数

`metrics` 命令本身不接受位置参数，需通过子命令操作。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | 显示帮助信息并退出 |

## 子命令

### metrics show

显示收集到的运行时指标。

```bash
autoship metrics show [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | 以 JSON 格式输出 |
| - | `--reset` | `False` | 显示后重置指标 |

### metrics export

将收集到的运行时指标导出为 JSON 文件。

```bash
autoship metrics export [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| `-o` | `--output PATH` | `~/.autoship/metrics.json` | 指标 JSON 文件写入路径 |
| - | `--reset` | `False` | 导出后重置指标 |

## 示例

显示指标：

```bash
autoship metrics show
```

以 JSON 格式显示：

```bash
autoship metrics show --json
```

导出到默认路径：

```bash
autoship metrics export
```

导出到指定路径并清空指标：

```bash
autoship metrics export --output ./metrics.json --reset
```

## 输出说明 / 常见错误

- `--reset` 会清空已收集的指标，导出前请确认无需保留历史数据。
- 默认导出路径为 `~/.autoship/metrics.json`，请确保目录可写。

## 相关命令

- [doctor](./doctor.md) — 检查运行环境
- [config](./config.md) — 管理配置
