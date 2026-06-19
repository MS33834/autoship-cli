"""Ollama OpenAI-compatible endpoint adapter."""

from __future__ import annotations

import time
from typing import Any, cast

import httpx

from autoship.adapters.model_gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelGateway,
)
from autoship.exceptions import ModelGatewayError
from autoship.models.config import ModelBackendConfig


class OllamaGateway(ModelGateway):
    """Gateway for Ollama's ``/v1`` OpenAI-compatible endpoint."""

    def __init__(self, cfg: ModelBackendConfig) -> None:
        super().__init__(cfg)
        self.client = httpx.Client(
            base_url=str(cfg.base_url),
            timeout=cfg.timeout,
        )

    def health(self) -> bool:
        try:
            resp = self.client.get("/models", timeout=5.0)
            return resp.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    def list_models(self) -> list[str]:
        resp = self.client.get("/models")
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or "data" not in data:
            raise ModelGatewayError("Unexpected response structure from Ollama: missing 'data'")
        models = cast(list[Any], data["data"])
        return [m["id"] for m in models if isinstance(m, dict) and "id" in m]

    def chat(self, req: ChatCompletionRequest) -> ChatCompletionResponse:
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
            resp = self.client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ModelGatewayError(f"Ollama returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            if isinstance(exc, httpx.TimeoutException):
                msg = "Ollama request timed out"
            else:
                msg = f"Ollama request failed: {exc}"
            raise ModelGatewayError(msg) from exc
        except ValueError as exc:
            raise ModelGatewayError("Ollama returned invalid JSON") from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelGatewayError("Unexpected response structure from Ollama") from exc
        return ChatCompletionResponse(
            content=content,
            model=data.get("model", self.cfg.model or ""),
            usage=data.get("usage"),
            latency_ms=(time.time() - start) * 1000,
        )
