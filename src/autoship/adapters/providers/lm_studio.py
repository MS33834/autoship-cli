"""LM Studio OpenAI-compatible endpoint adapter."""

from __future__ import annotations

from autoship.adapters.providers.openai_compatible import OpenAIGateway


class LmStudioGateway(OpenAIGateway):
    """Gateway for LM Studio's local OpenAI-compatible server."""

    DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1"
    HEALTH_PATH = "models"
    PROVIDER_NAME = "LM Studio"
