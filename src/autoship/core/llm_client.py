"""Simple LLM client for the fix command supporting OpenAI-compatible APIs."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any

import httpx

from autoship.core.cache import DiskCache
from autoship.core.metrics import get_registry
from autoship.exceptions import ModelGatewayError
from autoship.models.config import LlmConfig, LlmProvider

logger = logging.getLogger("autoship")

PROVIDER_URLS: dict[LlmProvider, str] = {
    LlmProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
    LlmProvider.OPENROUTER: "https://openrouter.ai/api/v1/chat/completions",
    LlmProvider.OLLAMA: "http://localhost:11434/api/chat",
}


class AsyncLlmClient:
    """Asynchronous LLM client using ``httpx.AsyncClient``."""

    def __init__(self, config: LlmConfig, cache: DiskCache | None = None) -> None:
        self.config = config
        self.cache = cache

    def _base_url(self) -> str:
        if self.config.base_url:
            return str(self.config.base_url)
        return PROVIDER_URLS[self.config.provider]

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        if self.config.provider == LlmProvider.OPENROUTER:
            headers["HTTP-Referer"] = "https://autoship.dev"
            headers["X-Title"] = "AutoShip CLI"
        return headers

    def _payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if self.config.provider == LlmProvider.OLLAMA:
            return {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {"num_predict": self.config.max_tokens},
            }
        return {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
        }

    def _parse_response(self, data: dict[str, Any]) -> str:
        if self.config.provider == LlmProvider.OLLAMA:
            return str(data.get("message", {}).get("content", ""))
        choices = data.get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", ""))

    def _cache_key(self, messages: list[dict[str, str]]) -> str:
        payload = json.dumps(
            {
                "provider": self.config.provider.value,
                "model": self.config.model,
                "messages": messages,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat request asynchronously and return the assistant's reply."""
        registry = get_registry()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        cache_key = self._cache_key(messages)
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                registry.inc("llm_cache_hits", description="LLM cache hits")
                return str(cached)
            registry.inc("llm_cache_misses", description="LLM cache misses")

        registry.inc("llm_requests", description="Total LLM requests")
        start = asyncio.get_event_loop().time()
        async with httpx.AsyncClient(
            headers=self._headers(), timeout=self.config.timeout
        ) as client:
            try:
                response = await client.post(
                    self._base_url(),
                    json=self._payload(messages),
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                registry.inc("llm_errors", description="LLM request errors")
                raise ModelGatewayError(f"LLM request failed: {exc}") from exc
            finally:
                elapsed_ms = (asyncio.get_event_loop().time() - start) * 1000
                registry.record("llm_latency_ms", elapsed_ms, description="LLM request latency")

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            registry.inc("llm_errors", description="LLM request errors")
            raise ModelGatewayError(f"Invalid LLM response: {exc}") from exc

        result = self._parse_response(data)
        if self.cache is not None:
            self.cache.set(cache_key, result)
        return result

    async def health(self) -> bool:
        """Best-effort async health check. Only Ollama exposes a simple endpoint."""
        if self.config.provider != LlmProvider.OLLAMA:
            return True
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                response = await client.get("http://localhost:11434")
                return int(response.status_code) == 200
            except httpx.HTTPError:
                return False


class LlmClient:
    """Synchronous wrapper around :class:`AsyncLlmClient`."""

    def __init__(self, config: LlmConfig, cache: DiskCache | None = None) -> None:
        self._async = AsyncLlmClient(config, cache=cache)

    @property
    def config(self) -> LlmConfig:
        return self._async.config

    def _base_url(self) -> str:
        return self._async._base_url()  # pyright: ignore[reportPrivateUsage]

    def _headers(self) -> dict[str, str]:
        return self._async._headers()  # pyright: ignore[reportPrivateUsage]

    def _payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        return self._async._payload(messages)  # pyright: ignore[reportPrivateUsage]

    def _parse_response(self, data: dict[str, Any]) -> str:
        return self._async._parse_response(data)  # pyright: ignore[reportPrivateUsage]

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat request and return the assistant's reply."""
        return asyncio.run(self._async.chat(system_prompt, user_prompt))

    def health(self) -> bool:
        """Best-effort health check."""
        return asyncio.run(self._async.health())
