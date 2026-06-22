# AutoShip-CLI 快速上手指南

本指南基于 AutoShip-CLI 的真实命令行为编写，可直接复制命令执行。

## 安装

```bash
pip install autoship
# 或隔离安装
pipx install autoship
```

## 1. 初始化项目

在已有 Git 仓库的项目根目录执行：

```bash
autoship init
```

输出示例：

```text
Created .autoship.toml
```

生成的 `.autoship.toml` 示例：

```toml
# AutoShip configuration
schema_version = 1
project_type = "generic"

[model]
default_tier = 1
fallback = true

[[model.backends]]
provider = "ollama"
base_url = "http://127.0.0.1:11434/v1"
model = "qwen2.5:7b"
timeout = 30.0

[clean]
enabled = true
tools = ["autoflake", "black"]

[commit]
enabled = true
max_tokens = 512
conventional_commits = true
```

按项目类型初始化：

```bash
autoship init --type python
```

## 2. 环境诊断

运行 `doctor` 检查工具链、模型后端和插件依赖：

```bash
autoship doctor
# 结构化输出
autoship doctor --json
# CI 健康检查：存在 ERROR 时返回非零退出码
autoship doctor --fail-on-error
```

如果缺少 `autoflake`、`black` 等清理工具，会给出安装建议。如果本地模型（Ollama/LM Studio）未启动，`model-backend` 会显示 WARNING，这是正常的，不影响非 AI 命令。

## 3. 清理与格式化

```bash
autoship clean
```

输出示例：

```text
reformatted /path/to/project/hello.py

All done! ✨ 🍰 ✨
1 file reformatted.
Clean complete.
```

CI 场景下使用 `--check`，需要修改时返回非零退出码：

```bash
autoship clean --check
```

跳过交互确认：

```bash
autoship clean --yes
```

## 4. 运行验证

```bash
autoship verify pytest
autoship verify "python -m unittest discover"
```

失败时可在 `.autoship/error/` 目录查看脱敏后的错误摘要。`verify` 默认不调用 AI，需要 LLM 修复时请确保本地模型已启动。

## 5. 生成提交信息

暂存改动后运行：

```bash
autoship commit
```

如果已配置模型后端，AutoShip 会根据 diff 生成 Conventional Commits 风格的提交信息并提示确认；未配置模型时会提示你手动编辑。

直接指定提交信息（不调用 AI）：

```bash
autoship commit -m "fix: resolve upload timeout"
```

## 6. 上传产物

### PyPI

```bash
autoship upload --target pypi
```

### Docker

```bash
autoship upload --target docker --image myapp --tag 0.1.0
```

预览将要执行的动作而不真正上传：

```bash
autoship --dry-run upload --target pypi
```

## 7. 查看和管理插件

```bash
# 查看和管理插件
autoship plugin list

# 安装注册表插件
autoship plugin install docker-ship

# 查看插件注册表
autoship registry list

# 查看运行时指标
autoship metrics show
```

## 8. 常用全局选项

```bash
autoship --yes clean          # 跳过确认
autoship --dry-run upload ... # 空跑预览
autoship --verbose verify ... # 详细输出
autoship --lang zh --help     # 中文帮助
```

## 下一步

- 自定义模型后端：编辑 `.autoship.toml` 的 `[model.backends]`。
- 开发插件：参考 `examples/custom-plugin/` 和 `docs/plugin-development.md`。
- 团队配置：使用 `AUTOSHIP_` 环境变量覆盖白名单内的配置项。

完整命令参考请见 [docs/commands/index.md](./commands/index.md)。
