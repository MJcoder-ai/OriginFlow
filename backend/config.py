# backend/config.py
"""Application configuration settings.

Defines environment-driven settings using Pydantic for the backend application.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration accessed across the backend."""

    api_prefix: str = "/api/v1"
    database_url: str
    cors_origin_regex: str = r"http://(localhost|127\.0\.0\.1):\d+$"
    openai_api_key: str
    openai_model_router: str = "gpt-4o-mini"
    openai_model_agents: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 512
    commands_per_minute: int = 30

    # Datasheet extraction flags. These booleans control which parsing
    # strategies are applied by `run_parsing_job()`. They can be toggled
    # via environment variables or via a future API.
    use_rule_based: bool = True
    use_table_extraction: bool = True
    use_ai_extraction: bool = True
    use_ocr_fallback: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
