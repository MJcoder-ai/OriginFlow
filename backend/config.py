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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
