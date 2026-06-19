"""Route tasks to appropriate local model backends with fallback."""

from __future__ import annotations

import httpx

from autoship.adapters.model_gateway import ChatCompletionRequest, ChatMessage
from autoship.adapters.providers.ollama import OllamaGateway
from autoship.exceptions import ModelGatewayError
from autoship.models.config import AppConfig


class ModelRouter:
    """Select a model backend and tier for a given task."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def _gateways(self) -> list[OllamaGateway]:
        """Return configured gateway instances."""
        gateways: list[OllamaGateway] = []
        for backend in self.config.model.backends:
            if backend.provider.value == "ollama":
                gateways.append(OllamaGateway(backend))
        return gateways

    def _chat(self, messages: list[ChatMessage], task_type: str) -> str:
        """Send a chat request, falling back across healthy backends."""
        gateways = self._gateways()
        if not gateways:
            raise ModelGatewayError("No model backends configured")

        last_error: Exception | None = None
        for gateway in gateways:
            try:
                if gateway.health():
                    req = ChatCompletionRequest(messages=messages)
                    resp = gateway.chat(req)
                    return resp.content
            except (ModelGatewayError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_error = exc
                if not self.config.model.fallback:
                    break
                continue

        if last_error:
            raise ModelGatewayError(f"All model backends unhealthy: {last_error}") from last_error
        raise ModelGatewayError("All model backends are unhealthy")

    def select_backend(self, tier: int | None = None) -> OllamaGateway | None:
        """Return the first healthy configured backend, or None if all are unhealthy."""
        for gateway in self._gateways():
            try:
                if gateway.health():
                    return gateway
            except (ModelGatewayError, httpx.RequestError, httpx.TimeoutException):
                continue
        return None

    def chat(self, messages: list[ChatMessage], task_type: str) -> str:
        """Send a chat request and return the model's response text."""
        return self._chat(messages, task_type)

    def generate_commit_message(self, diff: str, stats: str) -> str:
        """Generate a commit message from diff and stats."""
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are an expert software engineer writing concise Git commit messages. "
                    "Use conventional commits format: type(scope): subject. "
                    "Types: feat, fix, refactor, docs, test, chore. "
                    "Keep the subject under 72 characters."
                ),
            ),
            ChatMessage(role="user", content=f"Git stats:\n{stats}\n\nDiff:\n{diff[:8000]}"),
        ]
        return self.chat(messages, "commit").strip()
