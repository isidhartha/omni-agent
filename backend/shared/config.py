"""Configuration management for OmniAgent."""

from __future__ import annotations

import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI provider keys
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Database
    database_url: str = Field(
        default="postgresql://omniagent:password@localhost:5432/omniagent",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # Security
    secret_key: str = Field(default="change-this-in-production", alias="SECRET_KEY")

    # Application
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_agent_iterations: int = Field(default=10, alias="MAX_AGENT_ITERATIONS")
    sandbox_timeout: int = Field(default=30, alias="SANDBOX_TIMEOUT")

    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    model_config = {"env_file": ".env", "populate_by_name": True}

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key != "your_openai_key_here")

    @property
    def has_anthropic(self) -> bool:
        return bool(
            self.anthropic_api_key
            and self.anthropic_api_key != "your_anthropic_key_here"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
