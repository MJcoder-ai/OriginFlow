from __future__ import annotations
"""
Thin, test-friendly shim for LLM/embedding clients.

Why:
- `planner_agent.py` imports `backend.services.ai_clients` but this module
  didn't exist in the new tree, breaking imports during test collection.
- We provide lazy factories that work in CI (no network access required).
"""
from typing import Any
import os


def get_openai_client() -> Any:  # pragma: no cover - trivial glue
    """
    Return a client-like object. If OPENAI_API_KEY is not set or the SDK
    is unavailable, return a stub that raises on use (tests don't call it).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    try:
        from openai import OpenAI  # type: ignore
        if api_key:
            return OpenAI(api_key=api_key)
    except Exception:
        pass
    class _Stub:
        def __getattr__(self, name: str) -> Any:
            raise RuntimeError("OpenAI client not configured for this environment")
    return _Stub()


def get_embeddings_client() -> Any:  # pragma: no cover - trivial glue
    """
    Same principle as above; return a stub if not configured.
    """
    return get_openai_client()