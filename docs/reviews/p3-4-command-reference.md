# P3-4 完整命令参考文档 — 多角色 Review

## Review 范围

- `docs/commands/` 中英文命令参考页
- `docs/commands.md` 迁移页面
- `docs/demo.md`、`docs/index.md`、`README.md` 链接更新
- `mkdocs.yml` 导航更新
- `src/autoship/cli/commands/config.py`（为补齐 `config` 命令新增）
- `src/autoship/cli/main.py`（callback 中增加 `config_path` 传递）
- `tests/cli/commands/test_config.py`（新增测试）
- `tests/conftest.py`（`typer_context` fixture 补齐 `config_path`）
- `pyproject.toml` / `uv.lock`（新增 `tomli-w` 依赖）

## 各角色 Review 结论

### 1. 文档/UX组

- **发现**：原 `docs/commands.md` 仅覆盖部分命令，且缺少 `fix`、`metrics`、`config` 等命令的详细说明。
- **建议**：按命令拆分为独立参考页，统一模板（概述、语法、参数、选项、示例、输出说明、相关命令）。
- **状态**：已修复，已生成 12 个中文命令页和 12 个英文命令页。

- **发现**：`docs/commands.md` 存在旧链接，但内容已过时。
- **建议**：保留为迁移页面，指向新的 `docs/commands/index.md`。
- **状态**：已修复。

- **发现**：`docs/demo.md` 与 `docs/index.md` 仍链接到旧的 `commands.md`。
- **建议**：更新为 `commands/index.md`。
- **状态**：已修复。

### 2. CLI 命令组

- **发现**：验收标准中要求的 `config` 命令尚未实现，导致无法为其编写真实文档。
- **建议**：新增 `autoship config` 命令，至少支持 `list`、`get`、`telemetry` 子命令，满足 P3-7 对遥测开关的需求。
- **状态**：已修复，`src/autoship/cli/commands/config.py` 已实现。

- **发现**：`config list` 早期版本直接使用 `model_dump()`，输出包含 `PosixPath` / `HttpUrl` / `None`，`tomli_w` 序列化失败。
- **建议**：使用 `model_dump(mode="json")` 并递归剔除 `None`，确保 TOML/JSON 输出均可序列化。
- **状态**：已修复。

### 3. 安全/合规组

- **发现**：`config list` 会打印完整配置，可能泄露 API key、SIEM token 等敏感值。
- **建议**：在输出前对敏感键进行脱敏。
- **状态**：已修复，配置输出中 `api_key`、`siem_token`、`base_url`、`cx`、`public_key` 均替换为 `***`。

- **发现**：`config telemetry --enable/disable` 直接写入项目配置文件，但未确认目标文件路径。
- **建议**：优先使用 `--config` 全局选项指定的路径，否则回退到项目根目录的 `.autoship.toml`。
- **状态**：已修复。

### 4. 发布/集成组

- **发现**：新增 `tomli-w` 依赖后需要同步更新 lock 文件。
- **建议**：运行 `uv add tomli-w` 并提交 `pyproject.toml` / `uv.lock` 变更。
- **状态**：已修复。

- **发现**：MkDocs 导航未包含英文命令参考。
- **建议**：在 `mkdocs.yml` 中新增 `Command Reference (EN)` 导航节点。
- **状态**：已修复。

### 5. 测试组

- **发现**：新增 `config` 命令缺少测试，可能拉低覆盖率。
- **建议**：补充 `tests/cli/commands/test_config.py`，覆盖 list 脱敏、get 成功/失败、telemetry 状态与写入。
- **状态**：已修复。

- **发现**：`tests/conftest.py` 中的 `typer_context` fixture 缺少 `config_path`，与未来访问 `ctx.obj["config_path"]` 的代码不兼容。
- **建议**：补齐 fixture。
- **状态**：已修复。

## 修复汇总

1. 新增 `docs/commands/index.md` 与 12 个中文命令页（init、clean、verify、fix、commit、upload、plugin、doctor、audit、registry、metrics、config）。
2. 新增 `docs/commands/en/index.md` 与 12 个英文命令页。
3. 重写 `docs/commands.md` 为迁移页面。
4. 更新 `docs/demo.md`、`docs/index.md`、`README.md` 中的命令参考链接。
5. 更新 `mkdocs.yml` 导航，包含中文与英文命令参考。
6. 新增 `src/autoship/cli/commands/config.py`，实现 `config list`、`config get`、`config telemetry`。
7. `src/autoship/cli/main.py` callback 将 `config_path` 存入 `ctx.obj`。
8. 新增 `tests/cli/commands/test_config.py` 与 `tests/conftest.py` fixture 更新。
9. `pyproject.toml` 新增 `tomli-w` 依赖，`uv.lock` 已同步。

## 验证结果

- `uv run ruff check src tests`：通过
- `uv run pyright`：通过
- `uv run pytest -m 'not integration'`：**526 passed, 31 deselected**，覆盖率 87.84%
- `uv run bandit -r src -ll`：无新增问题
- `uv run mkdocs build --strict`：通过
- 实际 CLI 验证：`autoship config list`、`autoship config get model.default_tier`、`autoship config telemetry --enable/disable/status` 均可正常工作。
