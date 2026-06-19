"""OpenRouter API gateway."""

from __future__ import annotations

from autoship.adapters.model_gateway import ChatCompletionRequest, ChatCompletionResponse
from autoship.adapters.providers.openai_compatible import OpenAIGateway as _OpenAIGatewayBase
from autoship.exceptions import ModelGatewayError
from autoship.models.config import ModelBackendConfig


class OpenRouterGateway(_OpenAIGatewayBase):
    """Gateway for OpenRouter's API."""

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    HEALTH_PATH = "models"
    PROVIDER_NAME = "OpenRouter"

    def __init__(self, cfg: ModelBackendConfig) -> None:
        super().__init__(cfg)
        self.client.headers["HTTP-Referer"] = "https://autoship.dev"
        self.client.headers["X-Title"] = "AutoShip CLI"

    def _require_api_key(self) -> None:
        if not self.cfg.api_key:
            raise ModelGatewayError(
                f"{self.PROVIDER_NAME} requires an API key; "
                "configure it via the backend ``api_key`` field"
            )

    def health(self) -> bool:
        self._require_api_key()
        return super().health()

    def chat(self, req: ChatCompletionRequest) -> ChatCompletionResponse:
        self._require_api_key()
        return super().chat(req)
