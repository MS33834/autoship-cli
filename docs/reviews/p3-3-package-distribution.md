# P3-3 安装包与分发验证 — 多角色 Review

## Review 范围

- `src/autoship/__main__.py`
- `src/autoship/cli/main.py`
- `pyproject.toml`
- `autoship-sdk/pyproject.toml`
- `tests/integration/package/`

## 各角色 Review 结论

### 1. 发布/集成组

- **发现**：P3-3 缺少自动化验证，仅通过单元测试 mock 无法确认真实 wheel/sdist 安装后的行为。
- **建议**：新增集成测试，实际执行 `python -m build`，在干净 venv 中 `pip install` 后验证 entry point 与非 AI 命令。
- **状态**：已修复。

- **发现**：验收标准要求 sdist 也能成功安装。
- **建议**：补充 sdist 安装 + entry point 验证。
- **状态**：已修复，新增 `test_sdist_installs_and_runs`。

### 2. 基础设施/测试组

- **发现 1**：最初每个测试都独立 build wheel，耗时较长（约 2.5 分钟）。
- **建议**：将 `autoship_wheel`、`autoship_sdist`、`sdk_wheel` 设为 session scope，复用构建产物。
- **状态**：已修复，时间基本不变，主要耗时来自多个 venv 创建，但构建产物复用减少了磁盘 I/O。

- **发现 2**：`test_autoship_sdk.py` 中直接定义了 `sdk_wheel` fixture，导致 `test_sdk_installs_and_imports` 需要跨文件引用 `autoship_wheel` 时失败。
- **建议**：将 wheel fixtures 统一放到 `conftest.py`。
- **状态**：已修复。

### 3. 安全/合规组

- **发现**：干净环境测试不安装 `ai` extras，可验证非 AI 命令不硬依赖 `openai`。
- **建议**：保持当前设计，不需要额外修改。
- **状态**：无需修改。

## 修复汇总

1. 新增 `tests/integration/package/__init__.py`、`conftest.py`。
2. 新增 `tests/integration/package/test_package_install.py`，覆盖：
   - wheel 构建成功
   - `autoship --help` entry point 可用
   - `python -m autoship --help` 可用
   - `autoship init --yes` 在干净项目运行
   - `autoship doctor --json` 运行
   - `autoship upload --dry-run --target pypi` 运行
   - `autoship plugin list` 运行
   - `autoship verify "python --version"` 运行
   - sdist 安装后 entry point 可用
3. 新增 `tests/integration/package/test_autoship_sdk.py`，覆盖：
   - autoship-sdk wheel 构建成功
   - 干净 venv 中导入成功
   - `pip check` 无依赖冲突
4. wheel/sdist fixtures 设为 session scope，使用 `tmp_path_factory`。

## 验证结果

- `ruff check src tests`：通过
- `pyright`：通过
- `pytest -q -m 'not integration' --no-cov`：**521 passed, 30 deselected**
- `pytest tests/integration/package -q --no-cov`：**12 passed**（约 2 分 23 秒）
