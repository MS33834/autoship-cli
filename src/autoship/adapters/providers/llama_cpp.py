"""llama.cpp server OpenAI-compatible endpoint adapter."""

from __future__ import annotations

from autoship.adapters.providers.openai_compatible import OpenAIGateway


class LlamaCppGateway(OpenAIGateway):
    """Gateway for llama.cpp server's OpenAI-compatible endpoint."""

    DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"
    HEALTH_PATH = "/health"
    PROVIDER_NAME = "llama.cpp"
