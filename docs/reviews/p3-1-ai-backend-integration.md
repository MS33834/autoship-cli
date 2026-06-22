# P3-1 AI 路径真实后端联测 — 多角色 Review

## Review 范围

- `src/autoship/adapters/providers/ollama.py`
- `src/autoship/adapters/providers/openai_compatible.py`
- `tests/integration/ai_backends/conftest.py`
- `tests/integration/ai_backends/test_ollama.py`
- `tests/integration/ai_backends/test_lm_studio.py`
- `tests/adapters/test_ollama.py`
- `.github/workflows/ci.yml`
- `pyproject.toml`

## 各角色 Review 结论

### 1. AI/模型组

- **发现**：原 `OllamaGateway` 直接调用 `/models` 与 `/chat/completions` 绝对路径，对应的是自定义端点，不是标准 Ollama OpenAI-compatible API（应为 `/v1/models` 与 `/v1/chat/completions`）。这会导致集成测试在真实 Ollama 上失败。
- **建议**：将 `OllamaGateway` 改为继承 `OpenAIGateway`，使用相对路径，并设置默认 `base_url` 为 `http://localhost:11434/v1`。
- **状态**：已修复。

### 2. 基础设施/测试组

- **发现 1**：`test_ollama_chat_missing_model_raises` 与 `test_lm_studio_chat_missing_model_raises` 使用字典构造 messages，与其他测试不一致。
- **建议**：统一使用 `ChatMessage` 对象。
- **状态**：已修复。

- **发现 2**：CI 中 `uv run pytest -q` 会默认探测真实后端，虽然最终会 skip，但会增加 CI 耗时且不稳定。
- **建议**：CI 默认排除 `integration` 标记测试；新增 `workflow_dispatch` 触发的 `ai-backend-integration` job，在有真实后端时手动运行。
- **状态**：已修复。

- **发现 3**：`pytest.mark.integration` 在 `tests/integration/` 子目录下被识别为 unknown mark，因为该目录有独立的 `pytest.ini`。
- **建议**：在 `tests/integration/pytest.ini` 中注册 `integration` marker。
- **状态**：已修复。

### 3. 安全/合规组

- **发现**：API key 通过 `LM_STUDIO_API_KEY` 环境变量读取并传入 `ModelBackendConfig`，无硬编码；`pytest.skip` 信息包含后端 URL，属于测试输出，风险可控。
- **建议**：探测超时保持 2 秒合理；后端聊天 timeout 保持 30 秒。
- **状态**：无需修改。

## 修复汇总

1. `OllamaGateway` 重写为 `OpenAIGateway` 子类，使用标准 `/v1` OpenAI-compatible 端点。
2. 更新 `tests/adapters/test_ollama.py` 中的 URL 与 base_url 以匹配新标准。
3. 统一集成测试中的 `ChatMessage` 使用。
4. 在 `pyproject.toml` 与 `tests/integration/pytest.ini` 中注册 `integration` marker。
5. 更新 CI：默认排除 integration 测试，新增手动触发的 `ai-backend-integration` job。
6. 新增 `tests/integration/ai_backends/test_ollama.py` 与 `test_lm_studio.py`，覆盖 health、list_models、chat、模型缺失错误、ModelRouter 选择/生成、不可达后端等场景。

## 验证结果

- `ruff check src tests`：通过
- `pyright`：通过
- `pytest -q -m 'not integration' --no-cov`：514 passed, 16 deselected
- `pytest tests/integration/ai_backends -v --no-cov`：16 skipped（环境无真实后端时正确跳过）
