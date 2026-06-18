"""Tests for the model router."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autoship.adapters.model_gateway import ChatCompletionResponse, ChatMessage
from autoship.core.model_router import ModelRouter
from autoship.exceptions import ModelGatewayError
from autoship.models.config import AppConfig, ModelBackendConfig, Provider


def _backend(base_url: str = "http://localhost:11434") -> ModelBackendConfig:
    return ModelBackendConfig(provider=Provider.OLLAMA, base_url=base_url, model="llama3")


def test_chat_raises_when_no_backends(project_root: Path) -> None:
    config = AppConfig(project_root=project_root)
    router = ModelRouter(config)
    with pytest.raises(ModelGatewayError, match="No model backends"):
        router.chat([ChatMessage(role="user", content="hi")], "test")


def test_chat_uses_healthy_backend(project_root: Path) -> None:
    config = AppConfig(project_root=project_root, model={"backends": [_backend()]})
    router = ModelRouter(config)
    gateway = MagicMock()
    gateway.health.return_value = True
    gateway.chat.return_value = ChatCompletionResponse(content="hello", model="llama3")
    with patch.object(router, "_gateways", return_value=[gateway]):
        result = router.chat([ChatMessage(role="user", content="hi")], "test")
    assert result == "hello"


def test_chat_falls_back_to_second_backend(project_root: Path) -> None:
    config = AppConfig(project_root=project_root, model={"backends": [_backend()]})
    router = ModelRouter(config)
    first = MagicMock()
    first.health.return_value = False
    second = MagicMock()
    second.health.return_value = True
    second.chat.return_value = ChatCompletionResponse(content="ok", model="llama3")
    with patch.object(router, "_gateways", return_value=[first, second]):
        result = router.chat([ChatMessage(role="user", content="hi")], "test")
    assert result == "ok"


def test_chat_raises_when_all_backends_unhealthy(project_root: Path) -> None:
    config = AppConfig(project_root=project_root, model={"backends": [_backend()]})
    router = ModelRouter(config)
    gateway = MagicMock()
    gateway.health.return_value = False
    with (
        patch.object(router, "_gateways", return_value=[gateway]),
        pytest.raises(ModelGatewayError, match="All model backends are unhealthy"),
    ):
        router.chat([ChatMessage(role="user", content="hi")], "test")


def test_generate_commit_message(project_root: Path) -> None:
    config = AppConfig(project_root=project_root, model={"backends": [_backend()]})
    router = ModelRouter(config)
    with patch.object(router, "chat", return_value="feat(scope): add feature") as mock_chat:
        result = router.generate_commit_message(diff="diff", stats="stats")
    assert result == "feat(scope): add feature"
    args = mock_chat.call_args[0]
    messages: list[ChatMessage] = args[0]
    assert any(m.role == "system" for m in messages)
    assert any("Diff" in m.content for m in messages)
