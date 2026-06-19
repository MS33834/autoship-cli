"""Tests for the LLM client."""

from __future__ import annotations

import httpx
import pytest
import respx

from autoship.core.llm_client import AsyncLlmClient, LlmClient
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


def test_chat_success() -> None:
    with respx.mock:
        route = respx.post("https://api.openai.com/v1/chat/completions").respond(
            200, json={"choices": [{"message": {"content": "fix"}}]}
        )
        config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
        client = LlmClient(config)
        assert client.chat("system", "user") == "fix"
        assert route.called


def test_chat_http_error() -> None:
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            side_effect=httpx.ConnectError("offline")
        )
        config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
        client = LlmClient(config)
        with pytest.raises(ModelGatewayError, match="LLM request failed"):
            client.chat("system", "user")


def test_chat_invalid_json() -> None:
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").respond(200, text="not json")
        config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
        client = LlmClient(config)
        with pytest.raises(ModelGatewayError, match="Invalid LLM response"):
            client.chat("system", "user")


def test_health_non_ollama() -> None:
    config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
    client = LlmClient(config)
    assert client.health() is True


def test_health_ollama_ok() -> None:
    with respx.mock:
        route = respx.get("http://localhost:11434").respond(200)
        config = LlmConfig(provider=LlmProvider.OLLAMA)
        client = LlmClient(config)
        assert client.health() is True
        assert route.called


def test_health_ollama_error() -> None:
    with respx.mock:
        respx.get("http://localhost:11434").mock(side_effect=httpx.ConnectError("offline"))
        config = LlmConfig(provider=LlmProvider.OLLAMA)
        client = LlmClient(config)
        assert client.health() is False


@pytest.mark.asyncio
async def test_async_chat_success() -> None:
    with respx.mock:
        route = respx.post("https://api.openai.com/v1/chat/completions").respond(
            200, json={"choices": [{"message": {"content": "async fix"}}]}
        )
        config = LlmConfig(provider=LlmProvider.OPENAI, api_key="key")
        client = AsyncLlmClient(config)
        assert await client.chat("system", "user") == "async fix"
        assert route.called
