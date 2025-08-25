# backend/api/deps.py
"""
FastAPI dependency helpers.

NOTE:
- We intentionally avoid importing legacy ``backend.services.ai_service`` or
  ``AiOrchestrator`` here to prevent ``ModuleNotFoundError`` observed previously.
- The orchestrator is invoked via the /ai/act endpoint; this module should
  only provide common dependencies like DB sessions and shared services.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Request

# ``openai`` is an optional dependency. Import lazily so modules that depend on
# this file (e.g. during tests) don't fail to import if the package isn't
# installed. The route that actually uses the client will raise a runtime error
# when called without the library available.
try:  # pragma: no cover - import guard
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - fallback when library missing
    class AsyncOpenAI:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - simple stub
            raise RuntimeError("openai package is required for AI features")

from backend.database.session import get_session
from backend.services.anonymizer_service import AnonymizerService
from backend.services.embedding_service import EmbeddingService
from backend.config import settings
try:  # pragma: no cover - auth is optional
    from backend.auth.dependencies import get_current_user
except Exception:  # pragma: no cover - missing deps
    def get_current_user(*args, **kwargs):  # type: ignore[unused-ignore]
        raise RuntimeError("Authentication dependencies not installed")


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


__all__ = [
    "get_session",
    "get_ai_client",
    "get_anonymizer",
    "get_embedder",
    "get_current_user",
]
