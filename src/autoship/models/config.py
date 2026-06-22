"""Pydantic schemas for AutoShip configuration."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, Field, HttpUrl


class Provider(str, Enum):
    """Supported model backend providers."""

    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    OPENROUTER = "openrouter"


class ModelBackendConfig(BaseModel):
    """Configuration for a single model backend endpoint."""

    provider: Provider
    base_url: HttpUrl
    api_key: str | None = Field(default=None, repr=False)
    api_version: str | None = None
    model: str | None = None
    tier: Literal[1, 2, 3] = 2
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
    allowed_editors: list[str] = Field(
        default_factory=lambda: [
            "vim",
            "nvim",
            "vi",
            "emacs",
            "nano",
            "code",
            "subl",
            "micro",
            "helix",
            "hx",
        ],
        description="Allowed editors for the commit command. Only the first token of $EDITOR is used.",
    )


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
    BRAVE = "brave"
    GOOGLE = "google"
    SEARXNG = "searxng"


class AuditConfig(BaseModel):
    """Configuration for audit logging and enterprise forwarding."""

    log_dir: Path | None = None
    siem_enabled: bool = False
    siem_url: HttpUrl | None = None
    siem_token: str | None = Field(default=None, repr=False)
    retention_days: int = 30
    redact_unknown_fields: bool = False
    siem_max_failures: int = 3


class SandboxConfig(BaseModel):
    """Configuration for sandbox isolation requirements."""

    required: bool = True


class TelemetryConfig(BaseModel):
    """Configuration for anonymous telemetry collection.

    Telemetry is disabled by default. When enabled, only command name, exit
    code, duration, exception type/line, Python version, and platform family
    are collected. No file contents, paths, tokens, arguments, or environment
    variables are ever sent.
    """

    enabled: bool = False
    endpoint: HttpUrl | None = Field(
        default=None,
        description="Optional HTTPS endpoint for telemetry uploads.",
    )
    batch_size: int = Field(default=10, ge=1, le=100)
    timeout: float = Field(default=5.0, gt=0.0, le=30.0)
    allow_untrusted_endpoint: bool = False


class WebSearchConfig(BaseModel):
    """Configuration for the web-search plugin.

    Web search is disabled by default and must be explicitly enabled, because it
    sends error snippets to a public search service.
    """

    enabled: bool = False
    provider: WebSearchProvider = WebSearchProvider.DUCKDUCKGO
    api_key: str | None = Field(default=None, repr=False)
    cx: str | None = Field(default=None, repr=False)
    instance_url: str | None = None
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

    url: HttpUrl = cast(
        HttpUrl,
        "https://raw.githubusercontent.com/autoship-cli/autoship-cli/main/registry/plugins.json",
    )
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    public_key: str | None = Field(
        default=None,
        description="Base64-encoded Ed25519 public key used to verify the registry index.",
    )


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
    api_version: str | None = None
    base_url: HttpUrl | None = None
    timeout: float = 60.0
    max_tokens: int = 2048


class CacheConfig(BaseModel):
    """Configuration for the local disk cache."""

    enabled: bool = True
    ttl: int = 3600
    dir: Path | None = None


class VerifyConfig(BaseModel):
    """Configuration for the ``verify`` command."""

    allowed_commands: list[str] = Field(
        default_factory=lambda: [
            "pytest",
            "python",
            "python3",
            "ruff",
            "mypy",
            "black",
            "isort",
            "tox",
            "nox",
            "npm",
            "yarn",
            "pnpm",
            "poetry",
            "make",
        ]
    )


class ToolConfig(BaseModel):
    """Configuration for a single external tool."""

    path: str | None = None
    sha256: str | None = None


class ToolsConfig(BaseModel):
    """Configuration for external tool paths and optional SHA-256 verification."""

    git: ToolConfig = Field(default_factory=ToolConfig)
    docker: ToolConfig = Field(default_factory=ToolConfig)
    twine: ToolConfig = Field(default_factory=ToolConfig)
    gh: ToolConfig = Field(default_factory=ToolConfig)
    patch: ToolConfig = Field(default_factory=ToolConfig)

    def get(self, name: str) -> ToolConfig:
        """Return the configured tool or an empty default."""
        return getattr(self, name, ToolConfig())


class AppConfig(BaseModel):
    """Top-level application configuration."""

    schema_version: int = 1
    project_root: Path = Path(".")
    log_level: str = "INFO"
    audit_log_dir: Path | None = None
    locale: str = "auto"
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    # Backwards-compatible alias kept for legacy config files.
    telemetry_enabled: bool | None = Field(default=None, exclude=True)
    clean: CleanConfig = Field(default_factory=CleanConfig)
    commit: CommitConfig = Field(default_factory=CommitConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    verify: VerifyConfig = Field(default_factory=VerifyConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    docker_ship: DockerShipConfig = Field(default_factory=DockerShipConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    registry: RegistryConfig = Field(default_factory=RegistryConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)

    def model_post_init(self, __context: object) -> None:
        """Migrate legacy ``telemetry_enabled`` flag into ``telemetry.enabled``."""
        if self.telemetry_enabled is not None and not self.telemetry.enabled:
            self.telemetry.enabled = self.telemetry_enabled
