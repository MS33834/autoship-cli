"""Tests for the LLM client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from autoship.core.llm_client import LlmClient
from autoship.exceptions import ModelGatewayError
from autoship.models.config import LlmConfig, LlmProvider


def test_base_url_uses_provider_default() -> None:
    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    assert client._base_url() == "https://api.openai.com/v1/chat/completions"


def test_base_url_uses_custom_base_url() -> None:
    config = LlmConfig(
        provider=LlmProvider.OPENAI,
        api_key="key",
        base_url="https://example.com/v1",  # type: ignore[arg-type]
    )
    client = LlmClient(config)
    assert client._base_url() == "https://example.com/v1"


def test_headers_include_api_key() -> None:
    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="secret")
    client = LlmClient(config)
    assert client._headers()["Authorization"] == "Bearer secret"


def test_headers_without_api_key() -> None:
    config = LlmConfig(provider=LlmProvider.OLLAMA)
    client = LlmClient(config)
    assert "Authorization" not in client._headers()


def test_headers_openrouter() -> None:
    config = LlmConfig(provider=LlmProvider.OPENROUTER, api_key="key")
    client = LlmClient(config)
    headers = client._headers()
    assert headers["HTTP-Referer"] == "https://autoship.dev"
    assert headers["X-Title"] == "AutoShip CLI"


def test_payload_openai() -> None:
    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key", max_tokens=512)
    client = LlmClient(config)
    payload = client._payload([{"role": "user", "content": "hi"}])
    assert payload["model"] == "gpt-4o-mini"
    assert payload["max_tokens"] == 512
    assert payload["messages"][0]["content"] == "hi"


def test_payload_ollama() -> None:
    config = LlmConfig(provider=LlmProvider.OLLAMA, model="llama3", max_tokens=256)
    client = LlmClient(config)
    payload = client._payload([{"role": "user", "content": "hi"}])
    assert payload["model"] == "llama3"
    assert payload["stream"] is False
    assert payload["options"]["num_predict"] == 256


def test_parse_response_openai() -> None:
    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    assert client._parse_response({"choices": [{"message": {"content": "ok"}}]}) == "ok"


def test_parse_response_openai_no_choices() -> None:
    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    assert client._parse_response({"choices": []}) == ""


def test_parse_response_ollama() -> None:
    config = LlmConfig(provider=LlmProvider.OLLAMA)
    client = LlmClient(config)
    assert client._parse_response({"message": {"content": "hi"}}) == "hi"


@patch("autoship.core.llm_client.httpx.post")
def test_chat_success(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "fix"}}]}
    mock_post.return_value = mock_response

    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    assert client.chat("system", "user") == "fix"
    mock_post.assert_called_once()


@patch("autoship.core.llm_client.httpx.post")
def test_chat_http_error(mock_post: MagicMock) -> None:
    mock_post.side_effect = httpx.ConnectError("offline")

    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    with pytest.raises(ModelGatewayError, match="LLM request failed"):
        client.chat("system", "user")


@patch("autoship.core.llm_client.httpx.post")
def test_chat_invalid_json(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("bad json", "", 0)
    mock_post.return_value = mock_response

    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    with pytest.raises(ModelGatewayError, match="Invalid LLM response"):
        client.chat("system", "user")


def test_health_non_ollama() -> None:
    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    assert client.health() is True


@patch("autoship.core.llm_client.httpx.get")
def test_health_ollama_ok(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    config = LlmConfig(provider=LlmProvider.OLLAMA)
    client = LlmClient(config)
    assert client.health() is True


@patch("autoship.core.llm_client.httpx.get")
def test_health_ollama_error(mock_get: MagicMock) -> None:
    mock_get.side_effect = httpx.ConnectError("offline")

    config = LlmConfig(provider=LlmProvider.OLLAMA)
    client = LlmClient(config)
    assert client.health() is False
