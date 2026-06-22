# init

为当前项目初始化 AutoShip 配置文件，自动生成 `.autoship.toml` 并检测项目类型与硬件能力。

## 语法

```bash
autoship init [OPTIONS]
```

## 参数

`init` 命令不接受位置参数。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--type TEXT` | - | 强制指定项目类型 |
| `-o` | `--output PATH` | `.autoship.toml` | 配置文件输出路径 |
| `-y` | `--yes` | `False` | 跳过交互式确认 |

## 示例

在当前目录生成默认配置：

```bash
autoship init
```

输出示例：

```text
Created .autoship.toml
```

强制指定项目类型：

```bash
autoship init --type python
```

指定输出文件名：

```bash
autoship init -o autoship.toml
```

## 输出说明 / 常见错误

- 若当前目录已存在 `.autoship.toml`，使用 `--yes` 可直接覆盖，否则会提示确认。
- 执行失败时检查目录写入权限。

## 相关命令

- [clean](./clean.md) — 清理并格式化代码
- [doctor](./doctor.md) — 诊断环境是否满足运行要求
- [config](./config.md) — 查看和管理配置
