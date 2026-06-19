"""OpenAI commercial API gateway."""

from __future__ import annotations

from autoship.adapters.model_gateway import ChatCompletionRequest, ChatCompletionResponse
from autoship.adapters.providers.openai_compatible import OpenAIGateway as _OpenAIGatewayBase
from autoship.exceptions import ModelGatewayError


class OpenAIGateway(_OpenAIGatewayBase):
    """Gateway for OpenAI's commercial API."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    HEALTH_PATH = "models"
    PROVIDER_NAME = "OpenAI"

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
