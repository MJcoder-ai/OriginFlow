# backend/api/deps.py
"""FastAPI dependencies for database access and AI orchestrator."""
from __future__ import annotations

from functools import lru_cache

from openai import AsyncOpenAI

from backend.database.session import get_session
from backend.services.ai_service import AiOrchestrator
from backend.config import settings


@lru_cache
def get_ai_client() -> AsyncOpenAI:
    """Return a cached ``AsyncOpenAI`` client."""

    return AsyncOpenAI(api_key=settings.openai_api_key)


__all__ = ["get_session", "AiOrchestrator", "get_ai_client"]
