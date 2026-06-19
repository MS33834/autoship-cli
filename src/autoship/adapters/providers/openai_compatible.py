"""Shared OpenAI-compatible gateway implementation for local model backends."""

from __future__ import annotations

import asyncio
import time
from typing import Any, ClassVar, cast

import httpx

from autoship.adapters.model_gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelGateway,
)
from autoship.exceptions import ModelGatewayError
from autoship.models.config import ModelBackendConfig


class OpenAIGateway(ModelGateway):
    """Base class for OpenAI-compatible local model backends.

    Subclasses only need to declare their default base URL, health-check
    endpoint and a human-readable provider name.
    """

    DEFAULT_BASE_URL: ClassVar[str] = ""
    HEALTH_PATH: ClassVar[str] = "models"
    PROVIDER_NAME: ClassVar[str] = "openai"

    def __init__(self, cfg: ModelBackendConfig) -> None:
        super().__init__(cfg)
        base_url = str(cfg.base_url) if cfg.base_url else self.DEFAULT_BASE_URL
        headers: dict[str, str] = {}
        if cfg.api_key:
            headers["Authorization"] = f"Bearer {cfg.api_key}"
        self.client = httpx.Client(
            base_url=base_url,
            timeout=cfg.timeout,
            headers=headers,
        )

    def _health_url(self) -> str:
        if self.HEALTH_PATH.startswith("/"):
            return str(self.client.base_url.copy_with(path=self.HEALTH_PATH))
        return self.HEALTH_PATH

    def health(self) -> bool:
        try:
            resp = self.client.get(self._health_url(), timeout=5.0)
            return int(resp.status_code) == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    def list_models(self) -> list[str]:
        resp = self.client.get("models")
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or "data" not in data:
            raise ModelGatewayError(
                f"Unexpected response structure from {self.PROVIDER_NAME}: missing 'data'"
            )
        models = cast(list[Any], data["data"])
        return [m["id"] for m in models if isinstance(m, dict) and "id" in m]

    def _build_payload(self, req: ChatCompletionRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.cfg.model,
            "messages": [{"role": m.role, "content": m.content} for m in req.messages],
            "stream": False,
        }
        if req.max_tokens is not None:
            payload["max_tokens"] = req.max_tokens
        if req.temperature is not None:
            payload["temperature"] = req.temperature
        return payload

    async def achat(self, req: ChatCompletionRequest) -> ChatCompletionResponse:
        """Send a chat completion request asynchronously and return the response."""
        start = time.time()
        payload = self._build_payload(req)

        async with httpx.AsyncClient(
            base_url=self.client.base_url,
            timeout=self.cfg.timeout,
            headers=self.client.headers,
        ) as client:
            try:
                resp = await client.post("chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as exc:
                raise ModelGatewayError(
                    f"{self.PROVIDER_NAME} returned HTTP {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                if isinstance(exc, httpx.TimeoutException):
                    msg = f"{self.PROVIDER_NAME} request timed out"
                else:
                    msg = f"{self.PROVIDER_NAME} request failed: {exc}"
                raise ModelGatewayError(msg) from exc
            except ValueError as exc:
                raise ModelGatewayError(f"{self.PROVIDER_NAME} returned invalid JSON") from exc

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

    def chat(self, req: ChatCompletionRequest) -> ChatCompletionResponse:
        """Send a chat completion request and return the response."""
        return asyncio.run(self.achat(req))
