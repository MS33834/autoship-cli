"""Tests that provider error messages do not leak sensitive information."""

from __future__ import annotations

import httpx
import pytest
import respx

from autoship.adapters.model_gateway import ChatCompletionRequest, ChatMessage
from autoship.adapters.providers.azure_openai import AzureOpenAIGateway
from autoship.adapters.providers.ollama import OllamaGateway
from autoship.adapters.providers.openai import OpenAIGateway
from autoship.exceptions import ModelGatewayError
from autoship.models.config import ModelBackendConfig, Provider

OPENAI_BASE_URL = "https://api.openai.com/v1"
AZURE_BASE_URL = "https://my-resource.openai.azure.com/openai/deployments/my-deployment"
AZURE_API_VERSION = "2024-02-01"
OLLAMA_BASE_URL = "http://localhost:11434"


class _LeakyConnectError(httpx.ConnectError):
    """A connect error whose string representation embeds the request URL."""

    def __str__(self) -> str:
        return f"connection refused for {self.request.url}"


def _openai_gateway() -> OpenAIGateway:
    cfg = ModelBackendConfig(
        provider=Provider.OPENAI,
        base_url=OPENAI_BASE_URL,
        api_key="test-api-key",
        model="gpt-4o-mini",
        timeout=5.0,
    )
    return OpenAIGateway(cfg)


def _azure_gateway() -> AzureOpenAIGateway:
    cfg = ModelBackendConfig(
        provider=Provider.AZURE_OPENAI,
        base_url=AZURE_BASE_URL,
        api_key="test-api-key",
        api_version=AZURE_API_VERSION,
        model="gpt-4o",
        timeout=5.0,
    )
    return AzureOpenAIGateway(cfg)


def _ollama_gateway() -> OllamaGateway:
    cfg = ModelBackendConfig(
        provider=Provider.OLLAMA,
        base_url=OLLAMA_BASE_URL,
        model="llama3",
        timeout=5.0,
    )
    return OllamaGateway(cfg)


def _request() -> ChatCompletionRequest:
    return ChatCompletionRequest(messages=[ChatMessage(role="user", content="hi")])


@pytest.mark.parametrize(
    ("gateway", "endpoint"),
    [
        (_openai_gateway(), f"{OPENAI_BASE_URL}/chat/completions"),
        (_azure_gateway(), f"{AZURE_BASE_URL}/chat/completions"),
        (_ollama_gateway(), f"{OLLAMA_BASE_URL}/chat/completions"),
    ],
)
def test_chat_request_error_does_not_leak_base_url(gateway, endpoint: str) -> None:
    """Connection errors must not embed the backend URL in the exception text."""
    with respx.mock:
        respx.post(endpoint).mock(
            side_effect=_LeakyConnectError(
                "refused",
                request=httpx.Request("POST", endpoint),
            )
        )
        with pytest.raises(ModelGatewayError) as exc_info:
            gateway.chat(_request())

    message = str(exc_info.value)
    assert OPENAI_BASE_URL not in message
    assert AZURE_BASE_URL not in message
    assert OLLAMA_BASE_URL not in message
    assert "test-api-key" not in message


@pytest.mark.parametrize(
    ("gateway", "endpoint", "provider_name"),
    [
        (_openai_gateway(), f"{OPENAI_BASE_URL}/chat/completions", "OpenAI"),
        (_azure_gateway(), f"{AZURE_BASE_URL}/chat/completions", "Azure OpenAI"),
        (_ollama_gateway(), f"{OLLAMA_BASE_URL}/chat/completions", "Ollama"),
    ],
)
def test_chat_timeout_error_message(gateway, endpoint: str, provider_name: str) -> None:
    with respx.mock:
        respx.post(endpoint).mock(side_effect=httpx.TimeoutException("timeout"))
        with pytest.raises(ModelGatewayError, match=f"{provider_name} request timed out"):
            gateway.chat(_request())


@pytest.mark.parametrize(
    ("gateway", "endpoint", "provider_name"),
    [
        (_openai_gateway(), f"{OPENAI_BASE_URL}/chat/completions", "OpenAI"),
        (_azure_gateway(), f"{AZURE_BASE_URL}/chat/completions", "Azure OpenAI"),
        (_ollama_gateway(), f"{OLLAMA_BASE_URL}/chat/completions", "Ollama"),
    ],
)
def test_chat_http_status_error_message(gateway, endpoint: str, provider_name: str) -> None:
    with respx.mock:
        respx.post(endpoint).respond(500)
        with pytest.raises(ModelGatewayError, match=f"{provider_name} returned HTTP 500"):
            gateway.chat(_request())


@pytest.mark.parametrize(
    ("gateway", "endpoint", "provider_name"),
    [
        (_openai_gateway(), f"{OPENAI_BASE_URL}/chat/completions", "OpenAI"),
        (_azure_gateway(), f"{AZURE_BASE_URL}/chat/completions", "Azure OpenAI"),
        (_ollama_gateway(), f"{OLLAMA_BASE_URL}/chat/completions", "Ollama"),
    ],
)
def test_chat_invalid_json_error_message(gateway, endpoint: str, provider_name: str) -> None:
    with respx.mock:
        respx.post(endpoint).respond(200, text="not json")
        with pytest.raises(ModelGatewayError, match=f"{provider_name} returned invalid JSON"):
            gateway.chat(_request())


@pytest.mark.asyncio
async def test_achat_request_error_does_not_leak_base_url() -> None:
    with respx.mock:
        respx.post(f"{OPENAI_BASE_URL}/chat/completions").mock(
            side_effect=_LeakyConnectError(
                "refused",
                request=httpx.Request("POST", f"{OPENAI_BASE_URL}/chat/completions"),
            )
        )
        with pytest.raises(ModelGatewayError) as exc_info:
            await _openai_gateway().achat(_request())

    message = str(exc_info.value)
    assert OPENAI_BASE_URL not in message
    assert "test-api-key" not in message
