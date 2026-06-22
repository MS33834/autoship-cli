# P3-2 真实上传集成（PyPI / Docker）— 多角色 Review

## Review 范围

- `src/autoship/adapters/upload/pypi.py`
- `src/autoship/adapters/upload/docker.py`
- `src/autoship/adapters/upload/registry.py`
- `src/autoship/cli/commands/upload.py`
- `src/autoship/locales/en.json` / `zh.json`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `tests/adapters/upload/test_pypi.py`
- `tests/adapters/upload/test_docker.py`
- `tests/cli/commands/test_upload.py`
- `tests/e2e/test_end_to_end.py`
- `tests/integration/upload/`

## 各角色 Review 结论

### 1. 发布/集成组

- **发现 1**：原 `PyPIUploader` 只支持 `--repository`，无法区分测试与生产 URL，且默认 `pypi` 容易误传生产环境。
- **建议**：增加 `repository_url` 参数并默认使用 `testpypi`。
- **状态**：已修复。

- **发现 2**：`DockerUploader` 无法推送到本地 registry，不利于 CI/测试。
- **建议**：增加 `registry` 参数生成完整镜像名。
- **状态**：已修复。

- **发现 3**：CLI 缺少对应参数暴露。
- **建议**：`upload` 命令新增 `--repository`、`--repository-url`、`--registry`。
- **状态**：已修复。

### 2. 安全/合规组

- **发现**：`--repository-url` 可能被用于明文 HTTP 公网地址，存在凭证泄露风险。
- **建议**：仅允许 `https://` 或 `http://localhost/127.0.0.1/::1`。
- **状态**：已修复，新增 `PyPIUploader.is_safe_repository_url()` 并在 CLI 中校验。

- **建议**：默认 PyPI repository 改为 `testpypi`，避免误操作上传生产 PyPI。
- **状态**：已修复。

### 3. 基础设施/测试组

- **发现 1**：CLI 函数被单元测试直接调用时，typer 默认参数会变成 `OptionInfo` 对象，导致类型错误。
- **建议**：在函数入口用 `isinstance` 归一化参数；长期应让测试通过 Typer runner 调用。
- **状态**：已修复（入口归一化）。

- **发现 2**：真实 PyPI 集成测试需要可运行的本地 registry。使用 `pypiserver` 时发现 twine 默认 `/legacy/` 端点与 pypiserver 默认端点不匹配，且需要处理认证提示。
- **建议**：改为内置最小 HTTP server 实现 `/legacy/` 端点，避免外部服务依赖和路径不匹配问题。
- **状态**：已修复，移除了 `pypiserver` 依赖。

- **发现 3**：`python -m build` 在测试 venv 中不可用。
- **建议**：将 `build` 加入 dev 依赖。
- **状态**：已修复。

- **发现 4**：`tests/e2e/test_end_to_end.py::test_upload_dry_run` 断言默认 repository 为 `pypi`，与新的 `testpypi` 默认值冲突。
- **建议**：更新断言为 `testpypi`。
- **状态**：已修复。

- **发现 5**：CI 已默认排除 `integration` 测试，无需额外调整；新增参数需要在 `--help` 中正确显示。
- **状态**：已验证 `autoship upload --help` 输出包含新参数。

## 修复汇总

1. `PyPIUploader` 支持 `repository_url`，默认 `repository="testpypi"`，新增 `is_safe_repository_url()`。
2. `DockerUploader` 支持 `registry` 前缀，新增 `full_image` 属性。
3. `upload` registry factory 传递 `repository_url` 与 `registry`。
4. CLI `upload` 新增 `--repository`、`--repository-url`、`--registry`，并对 URL 做安全校验。
5. 更新中英文 i18n 选项说明。
6. `pyproject.toml` dev 依赖新增 `build`、`twine`。
7. 更新单元测试覆盖 repository-url 与 registry 路径。
8. 新增 `tests/integration/upload/test_pypi.py`：真实 build + twine upload 到本地 HTTP server。
9. 新增 `tests/integration/upload/test_docker.py`：Docker 可用时真实 build + push 到本地 registry。
10. 更新 `tests/e2e/test_end_to_end.py` 默认 repository 断言。

## 验证结果

- `ruff check src tests`：通过
- `pyright`：通过
- `pytest -q -m 'not integration' --no-cov`：**521 passed, 19 deselected**
- `pytest tests/integration/upload -q --no-cov`：**2 passed, 1 skipped**（Docker daemon 不可用）
- `autoship upload --help`：正确显示 `--repository`、`--repository-url`、`--registry`
