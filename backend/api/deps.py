# backend/api/deps.py
"""FastAPI dependencies for database access and AI orchestrator."""
from __future__ import annotations

from functools import lru_cache

from fastapi import Request
from openai import AsyncOpenAI

from backend.database.session import get_session
from backend.services.ai_service import AiOrchestrator
from backend.services.anonymizer_service import AnonymizerService
from backend.services.embedding_service import EmbeddingService
from backend.config import settings


@lru_cache
def get_ai_client() -> AsyncOpenAI:
    """Return a cached ``AsyncOpenAI`` client."""

    return AsyncOpenAI(api_key=settings.openai_api_key)


def get_anonymizer(request: Request) -> AnonymizerService:
    """Get the anonymizer service from app state."""
    return request.app.state.anonymizer


def get_embedder(request: Request) -> EmbeddingService:
    """Get the embedder service from app state."""
    return request.app.state.embedder


__all__ = ["get_session", "AiOrchestrator", "get_ai_client", "get_anonymizer", "get_embedder"]
