"""Shared fixtures and helpers for real model backend integration tests."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest

from autoship.adapters.model_gateway import ChatMessage
from autoship.models.config import AppConfig, ModelBackendConfig, ModelConfig, Provider


def _env_or_default(name: str, default: str) -> str:
    """Return environment variable or default, stripping trailing slashes."""
    return os.environ.get(name, default).rstrip("/")


@pytest.fixture(scope="module")
def ollama_base_url() -> str:
    """Ollama base URL from env or default."""
    return _env_or_default("OLLAMA_BASE_URL", "http://localhost:11434/v1")


@pytest.fixture(scope="module")
def ollama_model() -> str:
    """Ollama model name from env or default."""
    return os.environ.get("OLLAMA_MODEL", "llama3")


@pytest.fixture(scope="module")
def lm_studio_base_url() -> str:
    """LM Studio base URL from env or default."""
    return _env_or_default("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")


@pytest.fixture(scope="module")
def lm_studio_model() -> str:
    """LM Studio model name from env or default."""
    return os.environ.get("LM_STUDIO_MODEL", "local-model")


@pytest.fixture(scope="module")
def lm_studio_api_key() -> str | None:
    """Optional LM Studio API key."""
    return os.environ.get("LM_STUDIO_API_KEY") or None


def _probe(base_url: str, path: str, timeout: float = 2.0) -> bool:
    """Return True if the backend responds with 200 on the given path."""
    try:
        with httpx.Client(base_url=base_url, timeout=timeout) as client:
            response = client.get(path)
            return int(response.status_code) == 200
    except (httpx.RequestError, httpx.TimeoutException):
        return False


def ollama_available(base_url: str) -> bool:
    """Return True if Ollama is reachable at ``base_url``."""
    return _probe(base_url, "models")


def lm_studio_available(base_url: str) -> bool:
    """Return True if LM Studio is reachable at ``base_url``."""
    return _probe(base_url, "models")


def backend_config(
    provider: Provider,
    base_url: str,
    model: str,
    api_key: str | None = None,
    timeout: float = 30.0,
) -> ModelBackendConfig:
    """Build a ``ModelBackendConfig`` for integration tests."""
    return ModelBackendConfig(
        provider=provider,
        base_url=base_url,  # type: ignore[arg-type]
        model=model,
        api_key=api_key,
        timeout=timeout,
    )


def app_config_with_backend(
    project_root: Path, backend: ModelBackendConfig, fallback: bool = True
) -> AppConfig:
    """Return an ``AppConfig`` configured with a single backend."""
    return AppConfig(
        project_root=project_root,
        model=ModelConfig(backends=[backend], fallback=fallback),
    )


@pytest.fixture
def chat_messages() -> list[ChatMessage]:
    """A minimal chat prompt for integration tests."""
    return [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="Say 'hello' and nothing else."),
    ]
