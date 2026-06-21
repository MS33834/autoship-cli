"""Azure OpenAI API gateway."""

from __future__ import annotations

import time
from typing import Any

import httpx

from autoship.adapters.model_gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from autoship.adapters.providers._utils import format_provider_error
from autoship.adapters.providers.openai_compatible import OpenAIGateway as _OpenAIGatewayBase
from autoship.exceptions import ModelGatewayError


class AzureOpenAIGateway(_OpenAIGatewayBase):
    """Gateway for Azure OpenAI's API.

    The user supplies the full deployment endpoint as ``base_url``; ``api_version``
    is appended as the required ``api-version`` query parameter.
    """

    DEFAULT_BASE_URL = ""
    HEALTH_PATH = "models"
    PROVIDER_NAME = "Azure OpenAI"

    def _require_api_key(self) -> None:
        if not self.cfg.api_key:
            raise ModelGatewayError(
                f"{self.PROVIDER_NAME} requires an API key; "
                "configure it via the backend ``api_key`` field"
            )
        if not self.cfg.api_version:
            raise ModelGatewayError(
                f"{self.PROVIDER_NAME} requires an api_version; "
                "configure it via the backend ``api_version`` field"
            )

    def _api_version_param(self) -> dict[str, str]:
        return {"api-version": self.cfg.api_version or ""}

    def _health_url(self) -> str:
        url = super()._health_url()
        api_version = self.cfg.api_version
        if not api_version:
            return url
        if "?" in url:
            return f"{url}&api-version={api_version}"
        return f"{url}?api-version={api_version}"

    def health(self) -> bool:
        self._require_api_key()
        try:
            resp = self.client.get(self._health_url(), timeout=5.0)
            return int(resp.status_code) == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    def chat(self, req: ChatCompletionRequest) -> ChatCompletionResponse:
        self._require_api_key()
        start = time.time()
        payload: dict[str, Any] = {
            "model": self.cfg.model,
            "messages": [{"role": m.role, "content": m.content} for m in req.messages],
            "stream": False,
        }
        if req.max_tokens is not None:
            payload["max_tokens"] = req.max_tokens
        if req.temperature is not None:
            payload["temperature"] = req.temperature

        try:
            resp = self.client.post(
                "chat/completions",
                params=self._api_version_param(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
            raise ModelGatewayError(format_provider_error(self.PROVIDER_NAME, exc)) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelGatewayError(
                f"Unexpected response structure from {self.PROVIDER_NAME}"
            ) from exc

        return ChatCompletionResponse(
            content=content,
            model=data.get("model", self.cfg.model or ""),
            usage=data.get("usage"),
            latency_ms=(time.time() - start) * 1000,
        )
