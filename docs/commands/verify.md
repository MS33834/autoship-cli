# verify

运行验证命令，并在失败时支持 AI 辅助修复。`verify` 会捕获错误摘要并保存到 `.autoship/error/`，供后续 `fix` 命令使用。

## 语法

```bash
autoship verify [OPTIONS] COMMAND
```

## 参数

| 名称 | 是否必填 | 说明 |
|---|---|---|
| `command` | 是 | 要运行的验证命令，例如 `pytest`、`mypy src` |

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--fix` | `False` | 失败时调用模型生成修复建议 |

## 示例

运行 pytest：

```bash
autoship verify pytest
```

运行带参数的验证命令：

```bash
autoship verify "pytest tests/unit"
```

失败时请求 AI 修复建议：

```bash
autoship verify pytest --fix
```

## 输出说明 / 常见错误

- 验证失败时可在 `.autoship/error/` 目录查看脱敏后的错误摘要。
- `--fix` 会触发插件的 `on_error` Hook，收集 `FixSuggestion` 并提示用户应用补丁。
- 需要 LLM 修复时，请确保本地模型后端已启动并正确配置。

## 相关命令

- [fix](./fix.md) — 为最近一次验证失败生成修复建议
- [doctor](./doctor.md) — 检查模型后端与工具链
