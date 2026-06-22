# P3-6 错误消息与 UX 打磨 — 多角色 Review

## Review 范围

- `src/autoship/cli/main.py`（全局入口、异常处理、未知命令识别）
- `src/autoship/cli/commands/config.py`（配置命令错误与 help 文本）
- `src/autoship/cli/commands/upload.py`（上传命令错误与 help 文本）
- `src/autoship/cli/commands/plugin.py`（插件评分错误）
- `src/autoship/core/i18n.py`（i18n API 占位符冲突）
- `src/autoship/locales/zh.json` / `src/autoship/locales/en.json`
- `tests/cli/test_main.py`、`tests/cli/commands/test_config.py`、`tests/conftest.py`

## 各角色 Review 结论

### 1. 文档/UX组

- **发现**：`main.py` 中 app help、全局选项 help 均为硬编码英文，非英语用户无法看到本地化提示。
- **建议**：使用 `get_i18n()` 在 import 阶段加载本地化字符串作为 help；callback 选项 help 统一引用 locale key。
- **状态**：已修复，`main.py` 的 app help 与 `verbose/dry_run/yes/config_path/lang` 选项 help 已接入 `zh.json` / `en.json`。

- **发现**：`config.py` / `upload.py` 的 help 文本仍为英文硬编码，`config.py` 的 telemetry 状态提示也为英文。
- **建议**：将 config 子命令与 option help、telemetry 状态输出全部接入 i18n；upload 命令与选项 help 接入 i18n。
- **状态**：已修复。

### 2. 国际化/本地化组

- **发现**：`I18n._()` 方法第一位形参名为 `key`，导致任何使用 `{key}` 占位符的翻译模板在类型检查与调用时都可能冲突。
- **建议**：将形参改名为 `template_key`，释放 `key` 作为普通占位符。
- **状态**：已修复，`src/autoship/core/i18n.py:22` 改为 `template_key`；所有调用点无需修改。

- **发现**：测试环境未固定语言，依赖系统 locale 会导致中文环境下英文断言失败。
- **建议**：在 `tests/conftest.py` 中统一设置 `LANG=en_US.UTF-8`。
- **状态**：已修复。

### 3. 安全/合规组

- **发现**：未处理异常（非 AutoShipError）仅打印错误信息，没有引导用户自我诊断的入口。
- **建议**：在未处理异常分支输出 `error.suggestion.doctor`，引导运行 `autoship doctor`。
- **状态**：已修复。

### 4. CLI 命令组

- **发现**：`config.py` 中 `ConfigError` 直接抛出英文 f-string，未走 i18n；`get` 子命令错误输出直接写死 `Error:`。
- **建议**：统一使用 `i18n._("config.key_not_found")` 与 `i18n._("error.prefix")`。
- **状态**：已修复。

- **发现**：`upload.py` 的 repository_url 安全校验错误为英文硬编码。
- **建议**：接入 `upload.repository_url_invalid` key。
- **状态**：已修复。

- **发现**：`plugin.py` 的评分异常把底层 `ValueError` 直接字符串化抛出，未翻译。
- **建议**：接入 `plugin.rate_invalid`。
- **状态**：已修复。

### 5. 测试组

- **发现**：缺少对 `--help` 不输出 traceback、未知命令友好提示、错误后建议的 UX 测试。
- **建议**：在 `tests/cli/test_main.py` 新增三个 UX 测试。
- **状态**：已修复。

- **发现**：`test_config.py` 的 mock context 缺少 `i18n`，导致 `get_i18n_from_ctx` 回退到系统 locale。
- **建议**：补充 `i18n` 到 mock context。
- **状态**：已修复。

### 6. 性能/测试组

- **发现**：功能扩展后 import 阶段加载更多 locale 数据，`idle_memory` 基准从 14MB 上升到约 19.5MB，首次运行超出 1.2x 回归阈值。
- **建议**：确认内存仍在 100MB 目标内且涨幅合理后刷新 `benchmarks/results.json` 基线。
- **状态**：已修复，重新运行 benchmark 刷新基线，5/5 PASS。

## 修复汇总

1. `src/autoship/cli/main.py`：
   - app help、全局选项 help 接入 i18n。
   - 新增 `_known_commands`、`_is_unknown_command`，未知命令提前拦截并输出 `cli.unknown_command` 与建议。
   - 新增 `_print_suggestion`，针对 `ConfigError`、模型/API key、命令缺失、上传失败输出下一步操作建议。
   - 未处理异常后提示运行 `autoship doctor`。
2. `src/autoship/cli/commands/config.py`：
   - app/command/option help 与 telemetry 状态输出接入 i18n。
   - `ConfigError` 使用 `config.key_not_found`。
   - `get` 错误输出使用 `error.prefix`。
3. `src/autoship/cli/commands/upload.py`：
   - command/option help 接入 i18n。
   - repository_url 校验错误使用 `upload.repository_url_invalid`。
4. `src/autoship/cli/commands/plugin.py`：
   - 评分异常使用 `plugin.rate_invalid`。
5. `src/autoship/core/i18n.py`：
   - `_` 方法参数从 `key` 重命名为 `template_key`，避免占位符冲突。
6. `src/autoship/locales/zh.json` / `en.json`：
   - 新增 `config.*`、`upload.*`、`plugin.rate_invalid`、`cli.unknown_command.*`、`error.suggestion.*` 等键。
7. 测试：
   - `tests/cli/test_main.py` 新增 `--help` 无 traceback、未知命令友好提示、ConfigError 建议三个测试。
   - `tests/cli/commands/test_config.py` mock context 增加 `i18n`。
   - `tests/conftest.py` 设置 `LANG=en_US.UTF-8` 固定测试语言。
8. `benchmarks/results.json`：刷新为最新基线。

## 验证结果

- `uv run ruff check src tests dogfood benchmarks`：通过
- `uv run pyright`：0 errors
- `uv run pytest -m 'not integration'`：**529 passed, 31 deselected**，覆盖率 87.66%
- `uv run bandit -r src -ll`：无新增问题
- `uv run python dogfood/dogfood.py`：24/24 步骤通过，4/4 场景通过
- `uv run python benchmarks/benchmark.py`：全部 5 项基准 PASS
