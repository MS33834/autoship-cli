# doctor

诊断当前环境是否满足 AutoShip 运行要求。

## 语法

```bash
autoship doctor [OPTIONS]
```

## 参数

`doctor` 命令不接受位置参数。

## 选项

| 短选项 | 长选项 | 默认值 | 说明 |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | 以 JSON 格式输出诊断报告 |
| - | `--fail-on-error` | `False` | 存在 ERROR 时返回非零退出码 |

## 示例

运行常规诊断：

```bash
autoship doctor
```

结构化输出：

```bash
autoship doctor --json
```

CI 健康检查：

```bash
autoship doctor --fail-on-error
```

## 输出说明 / 常见错误

- 检查项包括：Python 版本、Git 配置、模型后端连通性、clean 工具链、插件外部依赖、审计/遥测目录权限等。
- 输出分级为 `OK` / `WARNING` / `ERROR`。
- 本地模型（Ollama/LM Studio）未启动时，`model-backend` 会显示 WARNING，这是正常的，不影响非 AI 命令。
- doctor 会根据 `project_type` 感知项目类型。非 Python 项目不会检查 `autoflake` / `black` 等 Python 工具链，避免无关的 ERROR 或 WARNING。

## 相关命令

- [init](./init.md) — 初始化项目配置
- [verify](./verify.md) — 运行验证
