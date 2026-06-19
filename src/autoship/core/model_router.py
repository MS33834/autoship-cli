"""Route tasks to appropriate local model backends with fallback."""

from __future__ import annotations

import httpx

from autoship.adapters.model_gateway import ChatCompletionRequest, ChatMessage, ModelGateway
from autoship.adapters.providers import (
    AzureOpenAIGateway,
    LlamaCppGateway,
    LmStudioGateway,
    OllamaGateway,
    OpenAIGateway,
    OpenRouterGateway,
    VllmGateway,
)
from autoship.core.metrics import get_registry
from autoship.exceptions import ModelGatewayError
from autoship.models.config import AppConfig, Provider

_PROVIDER_GATEWAYS: dict[Provider, type[ModelGateway]] = {
    Provider.OLLAMA: OllamaGateway,
    Provider.LM_STUDIO: LmStudioGateway,
    Provider.LLAMA_CPP: LlamaCppGateway,
    Provider.VLLM: VllmGateway,
    Provider.OPENAI: OpenAIGateway,
    Provider.AZURE_OPENAI: AzureOpenAIGateway,
    Provider.OPENROUTER: OpenRouterGateway,
}


class ModelRouter:
    """Select a model backend and tier for a given task."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def _gateways(self) -> list[ModelGateway]:
        """Return configured gateway instances."""
        gateways: list[ModelGateway] = []
        for backend in self.config.model.backends:
            gateway_cls = _PROVIDER_GATEWAYS.get(backend.provider)
            if gateway_cls is None:
                raise ModelGatewayError(
                    f"Unsupported model backend provider: {backend.provider.value}"
                )
            gateways.append(gateway_cls(backend))
        return gateways

    def _chat(self, messages: list[ChatMessage], task_type: str) -> str:
        """Send a chat request, falling back across healthy backends."""
        registry = get_registry()
        gateways = self._gateways()
        if not gateways:
            raise ModelGatewayError("No model backends configured")

        last_error: Exception | None = None
        attempts = 0
        for gateway in gateways:
            attempts += 1
            try:
                if gateway.health():
                    req = ChatCompletionRequest(messages=messages)
                    resp = gateway.chat(req)
                    registry.inc(
                        "model_backend_success",
                        description="Successful model backend requests",
                    )
                    if attempts > 1:
                        registry.inc(
                            "model_backend_fallbacks",
                            description="Model backend fallback occurrences",
                        )
                    return resp.content
            except (ModelGatewayError, httpx.RequestError, httpx.TimeoutException) as exc:
                registry.inc(
                    "model_backend_errors",
                    description="Model backend request errors",
                )
                last_error = exc
                if not self.config.model.fallback:
                    break
                continue

        if last_error:
            raise ModelGatewayError(f"All model backends unhealthy: {last_error}") from last_error
        raise ModelGatewayError("All model backends are unhealthy")

    def select_backend(self, tier: int | None = None) -> ModelGateway | None:
        """Return the first healthy configured backend, or None if all are unhealthy.

        When ``tier`` is provided, backends are filtered by their configured tier
        before health checks. If no backend in the requested tier is healthy and
        fallback is enabled, lower/higher tiers are considered.
        """
        gateways = self._gateways()
        if tier is not None:
            tier_gateways = [g for g in gateways if g.cfg.tier == tier]
            for gateway in tier_gateways:
                try:
                    if gateway.health():
                        return gateway
                except (ModelGatewayError, httpx.RequestError, httpx.TimeoutException):
                    continue
            if not self.config.model.fallback:
                return None
            # Fallback to other tiers.
            gateways = [g for g in gateways if g.cfg.tier != tier]
        for gateway in gateways:
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
