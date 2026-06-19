"""vLLM OpenAI-compatible endpoint adapter."""

from __future__ import annotations

from autoship.adapters.providers.openai_compatible import OpenAIGateway


class VllmGateway(OpenAIGateway):
    """Gateway for vLLM's OpenAI-compatible server."""

    DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
    HEALTH_PATH = "/health"
    PROVIDER_NAME = "vLLM"
