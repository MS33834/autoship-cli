# config

查看和管理 AutoShip 配置，包括生效配置、单个配置项和遥测开关。

## 语法

```bash
autoship config [OPTIONS] COMMAND [ARGS]...
```

## 参数

`config` 命令本身不接受位置参数，需通过子命令操作。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | 显示帮助信息并退出 |

## 子命令

### config list

显示生效配置（敏感值会被脱敏）。

```bash
autoship config list [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | 以 JSON 格式输出 |

### config get

获取单个配置值。

```bash
autoship config get [OPTIONS] KEY
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `key` | 是 | 点号分隔的配置键，例如 `model.default_tier` |

### config telemetry

启用、禁用或查看遥测设置。

```bash
autoship config telemetry [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--enable` | `False` | 启用遥测 |
| - | `--disable` | `False` | 禁用遥测 |
| - | `--status` | `False` | 显示当前遥测状态 |

## 示例

列出生效配置：

```bash
autoship config list
```

以 JSON 格式查看：

```bash
autoship config list --json
```

获取单个配置值：

```bash
autoship config get model.default_tier
```

查看遥测状态：

```bash
autoship config telemetry --status
```

启用遥测：

```bash
autoship config telemetry --enable
```

禁用遥测：

```bash
autoship config telemetry --disable
```

## 输出说明 / 常见错误

- `config list` 会对敏感值（如 API key）进行脱敏处理。
- 遥测默认关闭，仅在显式启用后才会上报匿名使用数据。
- 配置可通过 `.autoship.toml`、环境变量（白名单内）和命令行选项覆盖。

## 相关命令

- [init](./init.md) — 初始化配置文件
- [doctor](./doctor.md) — 检查配置与环境
