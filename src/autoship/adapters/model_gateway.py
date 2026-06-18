"""Abstract gateway for local model services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from autoship.models.config import ModelBackendConfig


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str
    content: str


@dataclass
class ChatCompletionRequest:
    """Request body for a chat completion."""

    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


@dataclass
class ChatCompletionResponse:
    """Response from a chat completion."""

    content: str
    model: str
    usage: dict[str, Any] | None = None
    latency_ms: float = 0.0


class ModelGateway(ABC):
    """Abstract base class for OpenAI-compatible local model backends."""

    def __init__(self, cfg: ModelBackendConfig) -> None:
        self.cfg = cfg

    @abstractmethod
    def health(self) -> bool:
        """Return True if the backend is reachable and healthy."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return a list of available model IDs."""

    @abstractmethod
    def chat(self, req: ChatCompletionRequest) -> ChatCompletionResponse:
        """Send a chat completion request and return the response."""
