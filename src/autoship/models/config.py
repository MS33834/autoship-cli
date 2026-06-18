"""Pydantic schemas for AutoShip configuration."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

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


class ModelConfig(BaseModel):
    """Configuration for model routing and fallback."""

    default_tier: Literal[1, 2, 3] = 2
    fallback: bool = True
    backends: list[ModelBackendConfig] = Field(default_factory=lambda: list[ModelBackendConfig]())


class AppConfig(BaseModel):
    """Top-level application configuration."""

    schema_version: int = 1
    project_root: Path = Path(".")
    log_level: str = "INFO"
    telemetry_enabled: bool = False
    audit_log_dir: Path | None = None
    clean: CleanConfig = Field(default_factory=CleanConfig)
    commit: CommitConfig = Field(default_factory=CommitConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
