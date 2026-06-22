# fix

请求 LLM 为最近一次验证失败生成修复建议。

## 语法

```bash
autoship fix [OPTIONS] [ERROR_FILE]
```

## 参数

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `error_file` | 否 | 错误日志路径，默认使用最近一次 `verify` 输出 |

## 选项

| 短选项 | 选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| `-y` | `--yes` | `False` | 跳过确认 |

## 示例

使用最近一次验证失败的错误日志：

```bash
autoship fix
```

指定错误日志文件：

```bash
autoship fix .autoship/error/verify_20250622.log
```

自动应用建议（需配合 `--yes`）：

```bash
autoship fix --yes
```

## 输出说明 / 常见错误

- 若找不到错误日志，会提示先运行 `autoship verify`。
- 修复建议需要本地模型后端可用；模型未启动时会显示 WARNING。

## 相关命令

- [verify](./verify.md) — 运行验证并生成错误摘要
- [doctor](./doctor.md) — 检查模型后端连通性
