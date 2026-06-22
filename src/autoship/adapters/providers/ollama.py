"""Ollama OpenAI-compatible endpoint adapter."""

from __future__ import annotations

from typing import ClassVar

from autoship.adapters.providers.openai_compatible import OpenAIGateway


class OllamaGateway(OpenAIGateway):
    """Gateway for Ollama's OpenAI-compatible ``/v1`` endpoint.

    Ollama exposes OpenAI-compatible APIs under ``/v1`` by default. This
    gateway reuses the shared OpenAI-compatible implementation and only
    declares Ollama-specific defaults.
    """

    DEFAULT_BASE_URL: ClassVar[str] = "http://localhost:11434/v1"
    HEALTH_PATH: ClassVar[str] = "models"
    PROVIDER_NAME: ClassVar[str] = "Ollama"
