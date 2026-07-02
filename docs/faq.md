# 常见问题（FAQ）

## 一般问题

### AutoShip 会上传我的代码吗？

不会。默认情况下，所有核心处理（清理、验证、提交信息生成）都在本地完成。只有当你显式配置外部模型后端（如 OpenAI）或上传目标（PyPI、Docker Registry）时，才会向对应服务发送必要数据。详见 [隐私政策](privacy.md)。

### 使用 AutoShip 需要联网吗？

核心命令（`init`、`clean`、`commit`、`verify`）可在完全离线环境下运行。需要联网的功能包括：

- `upload` 到 PyPI / Docker / GitHub
- `web-search` 插件的联网搜索
- `plugin install` 从 PyPI 或远程 registry 安装插件
- 使用云端模型后端

### AutoShip 支持哪些操作系统？

AutoShip 在 Linux、macOS 和 Windows 上均可运行。CI 也针对这三个平台构建二进制可执行文件。推荐 Python 版本为 3.10 及以上。

## 安装与升级

### 如何安装 AutoShip？

推荐方式：

```bash
pipx install autoship
```

或使用 uv：

```bash
uv tool install autoship
```

开发者可克隆仓库后使用 `uv sync --all-extras --dev` 安装。

### 如何升级到最新版本？

```bash
pipx upgrade autoship
# 或
pip install --upgrade autoship
```

### `autoship` 命令找不到怎么办？

1. 确认安装成功：`pipx list` 或 `pip show autoship`。
2. 检查 PATH 是否包含 pipx / Python scripts 目录。
3. 如果使用虚拟环境，确保已激活环境。

## 模型与 AI

### 可以使用 OpenAI / Claude / Azure 等云端模型吗？

可以。在 `.autoship.toml` 的 `[model.backends]` 中配置对应 provider，例如 `openai`、`azure_openai`、`openrouter`。API key 建议通过环境变量注入，避免写入配置文件。

```toml
[[model.backends]]
provider = "openai"
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key = "${OPENAI_API_KEY}"
```

### 本地模型推荐用什么？

- [Ollama](https://ollama.com/)：入门最简单，支持多种开源模型。
- [LM Studio](https://lmstudio.ai/)：带图形界面，适合本地实验。
- [llama.cpp](https://github.com/ggerganov/llama.cpp) 或 [vLLM](https://github.com/vllm-project/vllm)：适合有 GPU 的高级用户。

详见 [模型配置](models.md)。

### 模型后端连接失败怎么办？

1. 运行 `autoship doctor` 检查模型后端状态。
2. 确认后端服务已启动且 `base_url` 正确。
3. 检查防火墙或代理设置。
4. 查看日志：`autoship --verbose <command>`。

## 配置

### 配置文件放在哪里？

项目级配置：`.autoship.toml`（项目根目录）。

团队级配置：`.autoship.team.toml`（项目根目录，可被项目配置覆盖）。

全局配置：

- Linux/macOS：`~/.config/autoship/config.toml`
- Windows：`%APPDATA%\autoship\config.toml`

### 如何禁用遥测？

遥测默认已关闭。如需显式确认：

```toml
[telemetry]
enabled = false
```

### 如何切换语言？

```bash
autoship --lang en <command>
# 或在配置中
locale = "en"
```

## 插件

### 如何安装第三方插件？

```bash
autoship plugin install my-plugin
```

安装后默认为 `community` 信任等级。审阅源码后可提升为 `verified`：

```bash
autoship plugin trust my-plugin verified
```

### 如何开发自己的插件？

参考 [插件开发指南](plugin-development.md) 与示例插件 [`examples/custom-plugin`](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin)。

### 插件可以执行系统命令吗？

可以，但需要在 `permissions` 中声明 `shell = true`，并经过用户确认。建议遵循最小权限原则。

## 安全与审计

### AutoShip 如何保护我的凭证？

- 审计日志与错误日志默认脱敏 API key、token、密码等敏感信息。
- 建议通过环境变量注入密钥，避免写入配置文件。
- 配置文件权限由系统自动设置为仅所有者可读写。

### 审计日志保留多久？

默认保留 30 天。可通过 `.autoship.toml` 配置：

```toml
[audit]
retention_days = 30
```

手动清理：

```bash
autoship audit cleanup
```

### 发现安全漏洞如何报告？

请通过邮件 `security@autoship.dev` 私下报告，不要公开创建 issue。详见 [安全策略](security.md)。

## 故障排查

### `autoship verify` 失败但测试本身没问题？

`verify` 命令会先运行你指定的测试/检查命令，再运行 AutoShip 的验证流程。请检查：

1. 被调用的测试命令本身是否通过。
2. 是否有插件在 `pre_verify` / `post_verify` 阶段失败。
3. 使用 `--verbose` 查看详细日志。

### `autoship commit` 生成的消息不满意？

可以使用 `--edit` 进入编辑器修改生成的消息，或在配置中调整 `commit.max_tokens` 与 `conventional_commits`。

### 如何重置 AutoShip 配置？

删除项目根目录的 `.autoship.toml` 并重新运行 `autoship init`。

## 快速开始相关

### Quickstart 的 `verify --fix` 为什么报错说没有 AI 后端？

`verify --fix` 必须有可用 AI 模型才能生成修复建议。Quickstart 的「5 分钟无 AI 版」并未配置任何模型后端，因此直接调用 `verify --fix` 会报「no AI backend configured」。

- 若只想验证不修复：用 `autoship verify pytest`（不带 `--fix`）；
- 若要体验修复：按 Quickstart 的「+5 分钟带 AI 版」配置 Ollama，详见 [快速开始](quickstart.md)。
- 这是设计行为，非 bug，详见 [已知问题](known-issues.md)。

### Quickstart 跑完想体验完整 AI 功能怎么配？

1. 安装并启动 [Ollama](https://ollama.com/)；
2. 拉取一个模型：`ollama pull qwen2.5-coder:1.5b`（也可换更大模型）；
3. 在 `.autoship.toml` 中配置 `[model]` 段，`backend = "ollama"`；
4. 运行 `autoship doctor` 确认后端可达；
5. 体验 `autoship verify --fix pytest` 与 `autoship commit`（AI 生成 message）。

完整选项（含云端模型）见 [模型配置](models.md)。

### 如何选模型？

按场景选择：

- **入门 / 低配机器**：本地 Ollama + `qwen2.5-coder:1.5b` 或 `phi3:mini`，速度快、显存占用低。
- **本地高质量**：`qwen2.5-coder:7b`、`deepseek-coder:6.7b`，需要 8GB+ 显存。
- **云端高质量**：OpenAI `gpt-4o-mini` / `gpt-4o`、Anthropic Claude、Azure OpenAI，需联网与 API key。
- **隐私优先**：始终用本地模型，绝不配置云端 provider。

详见 [模型配置](models.md) 的选型表。

### 插件安装失败排查

`autoship plugin install <name>` 失败时按以下顺序排查：

1. 网络：能否访问 PyPI？`pip install <name>` 是否成功；
2. 信任等级：未审核的插件需先确认提示或显式 `autoship plugin trust <name> community`；
3. 权限：插件若声明 `shell = true`，需在交互确认中允许；
4. 兼容性：插件声明的 AutoShip 版本范围是否覆盖当前版本（`autoship --version`）；
5. 日志：`autoship --verbose plugin install <name>` 查看详细错误。

详见 [故障排查](troubleshooting.md)。

### 三语文档同步策略说明

- **源语言**：中文（zh）为源，en/ja 为翻译；
- **同步窗口**：新内容先在 zh 落地，en/ja 通常在数小时到数天内同步；
- **CI 校验**：i18n 完整性检查会对比三语文件清单，缺页或缺条目会告警；
- **命令代码块不翻译**：三语中的 shell / toml / yaml 代码块保持英文，仅注释与说明文字本地化；
- **链接相对路径**：跨页链接使用相对路径，三语目录结构保持一致（`docs/`、`docs/en/`、`docs/ja/`）。

如发现翻译滞后或缺漏，欢迎在 [GitHub Issues](https://github.com/MS33834/autoship-cli/issues) 提交。
