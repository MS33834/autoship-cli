"""Pydantic schemas for AutoShip configuration."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, Field, HttpUrl


class Provider(str, Enum):
    """Supported local model backend providers."""

    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"


class ModelBackendConfig(BaseModel):
    """Configuration for a single model backend endpoint."""

    provider: Provider
    base_url: HttpUrl
    api_key: str | None = Field(default=None, repr=False)
    model: str | None = None
    timeout: float = 30.0
    concurrency: int = 2
    priority: int = 0


class CleanConfig(BaseModel):
    """Configuration for the `clean` command."""

    enabled: bool = True
    tools: list[str] = ["autoflake", "black"]
    dry_run: bool = False
    exclude: list[str] = Field(default_factory=list)


class CommitConfig(BaseModel):
    """Configuration for the `commit` command."""

    enabled: bool = True
    max_tokens: int = 512
    conventional_commits: bool = True
    auto_push: bool = False


class SecurityThreshold(str, Enum):
    """Severity threshold for security scans."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SecurityConfig(BaseModel):
    """Configuration for the security-scan plugin."""

    enabled: bool = True
    tools: list[str] = ["bandit"]
    threshold: SecurityThreshold = SecurityThreshold.MEDIUM
    fail_fast: bool = True


class WebSearchProvider(str, Enum):
    """Supported web search backends."""

    DUCKDUCKGO = "duckduckgo"


class AuditConfig(BaseModel):
    """Configuration for audit logging and enterprise forwarding."""

    log_dir: Path | None = None
    siem_enabled: bool = False
    siem_url: HttpUrl | None = None
    siem_token: str | None = Field(default=None, repr=False)
    retention_days: int = 30


class WebSearchConfig(BaseModel):
    """Configuration for the web-search plugin.

    Web search is disabled by default and must be explicitly enabled, because it
    sends error snippets to a public search service.
    """

    enabled: bool = False
    provider: WebSearchProvider = WebSearchProvider.DUCKDUCKGO
    max_results: int = 3
    timeout: float = 10.0


class DockerShipConfig(BaseModel):
    """Configuration for the docker-ship plugin."""

    enabled: bool = True
    default_image: str | None = None
    default_tag: str = "latest"
    push: bool = False
    build_args: dict[str, str] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Configuration for model routing and fallback."""

    default_tier: Literal[1, 2, 3] = 2
    fallback: bool = True
    backends: list[ModelBackendConfig] = Field(default_factory=lambda: list[ModelBackendConfig]())


class RegistryConfig(BaseModel):
    """Configuration for the plugin registry client."""

    url: HttpUrl = cast(HttpUrl, "https://raw.githubusercontent.com/autoship-cli/autoship-cli/main/registry/plugins.json")
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600


class LlmProvider(str, Enum):
    """Supported LLM providers for the fix command."""

    OPENAI = "openai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class LlmConfig(BaseModel):
    """Configuration for the LLM-powered fix command."""

    provider: LlmProvider = LlmProvider.OPENAI
    model: str = "gpt-4o-mini"
    api_key: str | None = Field(default=None, repr=False)
    base_url: HttpUrl | None = None
    timeout: float = 60.0
    max_tokens: int = 2048


class AppConfig(BaseModel):
    """Top-level application configuration."""

    schema_version: int = 1
    project_root: Path = Path(".")
    log_level: str = "INFO"
    telemetry_enabled: bool = False
    audit_log_dir: Path | None = None
    locale: str = "auto"
    clean: CleanConfig = Field(default_factory=CleanConfig)
    commit: CommitConfig = Field(default_factory=CommitConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    docker_ship: DockerShipConfig = Field(default_factory=DockerShipConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    registry: RegistryConfig = Field(default_factory=RegistryConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
