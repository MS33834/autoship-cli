# audit

导出或清理审计日志。审计日志默认存放在项目根目录的 `.autoship/audit/` 下，可通过配置或环境变量调整。

## 语法

```bash
autoship audit [OPTIONS] COMMAND [ARGS]...
```

## 参数

`audit` 命令本身不接受位置参数，需通过子命令操作。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--help` | - | 显示帮助信息并退出 |

## 子命令

### audit export

将审计记录导出为 JSON Lines 文件。

```bash
autoship audit export [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| `-s` | `--since TEXT` | - | 仅导出该时间之后的记录（ISO 日期或 `1d`/`7d`/`30d`） |
| `-o` | `--output PATH` | - | 输出文件路径 |

### audit cleanup

删除超过保留期的审计日志文件。

```bash
autoship audit cleanup [OPTIONS]
```

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--retention-days INTEGER` | - | 保留天数 |
| - | `--dry-run` | `False` | 仅预览操作 |

## 示例

导出最近 30 天的审计记录：

```bash
autoship audit export --since 30d
```

导出到指定文件：

```bash
autoship audit export --since 2025-01-01 --output ./audit.jsonl
```

清理 90 天前的日志：

```bash
autoship audit cleanup --retention-days 90
```

预览将要删除的日志：

```bash
autoship audit cleanup --retention-days 90 --dry-run
```

## 输出说明 / 常见错误

- `--since` 支持 ISO 日期（如 `2025-01-01`）或相对天数（如 `1d`、`7d`、`30d`）。
- `--output` 未指定时，通常会写入默认路径（如 `./audit.jsonl`），具体行为取决于实现。
- 清理操作不可逆，建议先使用 `--dry-run` 预览。

## 相关命令

- [config](./config.md) — 查看和修改审计目录等配置
- [doctor](./doctor.md) — 检查审计目录权限
