# plugin

管理插件，包括列出已注册插件、搜索注册表、安装/卸载、评分、更新信任等级等。

## 语法

```bash
autoship plugin [OPTIONS] COMMAND [ARGS]...
```

## 参数

`plugin` 命令本身不接受位置参数，需通过子命令操作。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | 显示帮助信息并退出 |

## 子命令

### plugin list

列出已注册插件及其信任等级。

```bash
autoship plugin list
```

### plugin search

在官方插件注册表索引中搜索插件。

```bash
autoship plugin search [OPTIONS] [KEYWORD]
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `keyword` | 否 | 在插件名称或描述中搜索的关键词 |

### plugin info

显示注册表中某个插件的详细信息。

```bash
autoship plugin info [OPTIONS] NAME
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `name` | 是 | 插件名称 |

### plugin install

安装插件包并在本地注册。

```bash
autoship plugin install [OPTIONS] SOURCE
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `source` | 是 | 包描述符或注册表中的插件名称 |

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--name TEXT` | - | 注册时使用的插件名称 |
| - | `--version TEXT` | - | 插件版本 |
| - | `--trust LEVEL` | - | 初始信任等级：`builtin`、`verified`、`community`、`untrusted` |
| - | `--dry-run` | `False` | 仅预览操作 |
| `-y` | `--yes` | `False` | 跳过确认 |
| - | `--skip-trust-check` | `False` | 跳过信任等级警告 |
| - | `--no-sandbox` | `False` | 不使用沙箱运行 pip install |

### plugin uninstall

卸载插件包并从本地注册表中移除。

```bash
autoship plugin uninstall [OPTIONS] NAME
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `name` | 是 | 要卸载的插件名称 |

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--dry-run` | `False` | 仅预览操作 |
| `-y` | `--yes` | `False` | 跳过确认 |

### plugin rate

为已注册插件评分。

```bash
autoship plugin rate [OPTIONS] NAME SCORE
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `name` | 是 | 插件名称 |
| `score` | 是 | 评分，范围 1–5 |

### plugin stats

显示本地插件使用统计。

```bash
autoship plugin stats
```

### plugin trust

更新已注册插件的信任等级。

```bash
autoship plugin trust [OPTIONS] NAME LEVEL
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `name` | 是 | 插件名称 |
| `level` | 是 | 新信任等级：`builtin`、`verified`、`community`、`untrusted` |

### plugin update

检查并安装插件更新。

```bash
autoship plugin update [OPTIONS] [NAME]
```

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `name` | 否 | 要更新的插件名称 |

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--all` | `False` | 更新所有已注册插件 |
| - | `--dry-run` | `False` | 仅预览操作 |
| `-y` | `--yes` | `False` | 跳过确认 |
| - | `--skip-trust-check` | `False` | 跳过信任等级警告 |
| - | `--no-sandbox` | `False` | 不使用沙箱运行 pip install |

## 示例

列出已注册插件：

```bash
autoship plugin list
```

搜索注册表：

```bash
autoship plugin search docker
```

查看插件详情：

```bash
autoship plugin info docker-ship
```

安装注册表插件：

```bash
autoship plugin install docker-ship
```

安装本地插件并指定信任等级：

```bash
autoship plugin install ./local-plugin --trust verified
```

调整插件信任等级：

```bash
autoship plugin trust my-plugin verified
```

卸载插件：

```bash
autoship plugin uninstall my-plugin
```

更新所有插件：

```bash
autoship plugin update --all
```

## 输出说明 / 常见错误

- 信任等级：`builtin` > `verified` > `community` > `untrusted`。
- 安装未经验证的插件时会给出信任警告，可使用 `--skip-trust-check` 跳过。
- `--no-sandbox` 会禁用 pip 安装沙箱，仅在可信环境使用。

## 相关命令

- [registry](./registry.md) — 查看和同步插件注册表
- [doctor](./doctor.md) — 检查插件外部依赖
