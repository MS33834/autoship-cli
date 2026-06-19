"""Simple LLM client for the fix command supporting OpenAI-compatible APIs."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from autoship.exceptions import ModelGatewayError
from autoship.models.config import LlmConfig, LlmProvider

logger = logging.getLogger("autoship")

PROVIDER_URLS: dict[LlmProvider, str] = {
    LlmProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
    LlmProvider.OPENROUTER: "https://openrouter.ai/api/v1/chat/completions",
    LlmProvider.OLLAMA: "http://localhost:11434/api/chat",
}


class LlmClient:
    """Call an LLM with a prompt and return the generated text."""

    def __init__(self, config: LlmConfig) -> None:
        self.config = config

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

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat request and return the assistant's reply."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = httpx.post(
                self._base_url(),
                headers=self._headers(),
                json=self._payload(messages),
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ModelGatewayError(f"LLM request failed: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise ModelGatewayError(f"Invalid LLM response: {exc}") from exc

        return self._parse_response(data)

    def health(self) -> bool:
        """Best-effort health check. Only Ollama exposes a simple endpoint."""
        if self.config.provider != LlmProvider.OLLAMA:
            return True
        try:
            response = httpx.get("http://localhost:11434", timeout=2.0)
            return int(response.status_code) == 200
        except httpx.HTTPError:
            return False
