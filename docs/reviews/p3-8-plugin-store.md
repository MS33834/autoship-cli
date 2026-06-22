# P3-8 插件商店与发布流程 — 多角色 Review

## Review 范围

- `docs/plugin-publishing.md`（插件发布指南）
- `registry/plugins.json`（插件注册表数据）
- `registry/schema.json`（插件注册表 JSON Schema）
- `registry-web/app.js`、`registry-web/styles.css`（Web UI）
- `src/autoship/plugins/typecheck.py`（新增内置插件）
- `src/autoship/core/hook_dispatcher.py`（内置插件加载）
- `tests/plugins/test_typecheck.py`（新增插件测试）
- `mkdocs.yml`、`README.md`、`TASKS.md`

## 各角色 Review 结论

### 1. 生态/插件组

- **发现**：缺少面向插件作者的发布 SOP，签名/哈希与 PR 流程未文档化。
- **建议**：新增 `docs/plugin-publishing.md`，包含元数据格式、sha256 计算、PGP 签名示例、PR 模板、审核与下架流程。
- **状态**：已修复，`docs/plugin-publishing.md` 已创建并接入 `mkdocs.yml`。

- **发现**：`registry/plugins.json` 字段不一致：builtin 插件缺少 `permissions`，所有插件缺少 `audit_status`。
- **建议**：为每个条目补充 `permissions` 与 `audit_status`；新增 `typecheck` 内置插件以满足“至少 2 个真实插件”要求。
- **状态**：已修复，`registry/plugins.json` 已更新并新增 `typecheck` 条目。

### 2. 安全/合规组

- **发现**：没有正式的 schema 校验注册表数据，容易出现字段缺失或类型错误。
- **建议**：新增 `registry/schema.json`（JSON Schema draft-07），定义必填字段、`trust_level` 枚举、`audit_status` 枚举、sha256 正则、permissions 结构等。
- **状态**：已修复，`registry/schema.json` 已创建。

- **发现**：`docker-ship` 插件需要调用 `docker` 命令，属于 shell 权限；但 builtin 插件默认不会进入沙箱，因此权限声明主要用于展示。
- **建议**：在 `permissions` 中明确 `shell: true`，并在文档中说明 builtin/verified 插件直接在主进程运行，community/untrusted 进入沙箱。
- **状态**：已修复，`docker-ship` 的 `permissions.shell` 设为 `true`。

### 3. 前端/UX组

- **发现**：registry-web 目前只展示 `trust_level` 与 `publisher.verified`，缺少对 `audit_status` 的展示。
- **建议**：在卡片与弹窗中增加 `audit_status` 徽章，pending 显示黄色、approved 显示绿色、rejected 显示红色。
- **状态**：已修复，`registry-web/app.js` 增加 `auditStatusBadge`，`styles.css` 增加 `.audit-badge` 样式。

- **发现**：卡片 header 中 trust badge 独占一行，新增 audit badge 后需要并排显示。
- **建议**：用 `.badges` flex 容器包裹两个 badge。
- **状态**：已修复。

### 4. CLI 命令组

- **发现**：新增 `typecheck` 内置插件后，需要在 `HookDispatcher._load_builtin` 中注册，否则不会生效。
- **建议**：在 `src/autoship/core/hook_dispatcher.py` 中导入并注册 `typecheck.plugin`。
- **状态**：已修复。

- **发现**：`typecheck` 插件若直接调用 `pyright`，在缺少该工具的环境中会跳过；行为与 `security_scan` 一致。
- **建议**：保持降级逻辑，并补充单元测试覆盖成功、失败、跳过、dry-run 场景。
- **状态**：已修复，`tests/plugins/test_typecheck.py` 已创建。

### 5. 测试组

- **发现**：`test_typecheck.py` 中 `subprocess.run` 补丁可能因其他模块调用而误匹配。
- **建议**：使用 `patch("subprocess.run", ...)` 在测试函数内限定范围，并验证调用参数。
- **状态**：已按建议实现，测试验证 `cwd`、`capture_output`、`text` 参数。

## 修复汇总

1. `docs/plugin-publishing.md`：
   - 新建插件发布指南，定义元数据格式、sha256/签名要求、PR 模板、审核与下架流程。
2. `registry/schema.json`：
   - 新增 JSON Schema v2，用于校验 `registry/plugins.json`。
3. `registry/plugins.json`：
   - 所有条目补充 `permissions` 与 `audit_status`。
   - 新增内置插件 `typecheck`（真实实现，`audit_status: approved`）。
   - 更新 `updated_at` 为 2026-06-22。
4. `registry-web/app.js` / `styles.css`：
   - 增加 `auditStatusBadge` 与 `.audit-badge` 样式，在卡片和弹窗中展示审核状态。
5. `src/autoship/plugins/typecheck.py`：
   - 新增内置类型检查插件，在 `pre_commit` 钩子中调用 `pyright`，未安装时优雅跳过。
6. `src/autoship/core/hook_dispatcher.py`：
   - 在 `_load_builtin` 中注册 `typecheck.plugin`。
7. `tests/plugins/test_typecheck.py`：
   - 新增对跳过、成功、失败、dry-run 四种场景的单元测试。
8. `mkdocs.yml`：
   - 新增 `插件发布指南: plugin-publishing.md` 导航。
9. `README.md` / `TASKS.md`：
   - 将 P3-8 状态更新为已完成。

## 验证结果

- `uv run ruff check src tests registry-web`：通过
- `uv run pyright`：0 errors
- `uv run pytest`：**551 passed, 17 skipped**，覆盖率 87.73%
- `uv run bandit -r src -ll`：无新增问题
- `uv run python dogfood/dogfood.py`：24/24 步骤、4/4 场景通过
- `uv run python benchmarks/benchmark.py`：全部 5 项基准 PASS
