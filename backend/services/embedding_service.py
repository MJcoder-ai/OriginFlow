"""Embedding service for feedback logs and action queries.

This module wraps local and remote embedding models.  By default it
uses a SentenceTransformer model from the ``sentence-transformers``
package.  A fallback path can use OpenAI's embedding API if the
environment variable ``OPENAI_API_KEY`` is set and the local model
fails or is disabled.  Texts are concatenated from action metadata
before being embedded.
"""
from __future__ import annotations

import os
from typing import List, Optional, Any

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:
    SentenceTransformer = None  # type: ignore

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    OpenAI = None  # type: ignore


class EmbeddingService:
    """Service to convert text input into embedding vectors."""

    def __init__(self, model_name: str | None = None, openai_api_key: str | None = None) -> None:
        self.model_name = model_name or os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.local_model: Optional[SentenceTransformer] = None
        if SentenceTransformer is not None:
            try:
                self.local_model = SentenceTransformer(self.model_name)
            except Exception:
                self.local_model = None
        self.openai_client: Optional[OpenAI] = None
        if OpenAI is not None and self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)

    async def embed_text(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts into vectors."""
        if self.local_model:
            embeddings = self.local_model.encode(texts, convert_to_numpy=False)
            return [list(vec) for vec in embeddings]
        if not self.openai_client:
            raise RuntimeError("No embedding model available")
        response = self.openai_client.embeddings.create(
            input=texts,
            model="text-embedding-3-small",
        )
        return [d.embedding for d in response.data]

    async def embed_log(self, payload: Any, anonymized_prompt: str, anonymized_context: dict) -> List[float]:
        """Embed an enriched feedback log."""
        proposed = payload.proposed_action if hasattr(payload, "proposed_action") else payload.get("proposed_action", {})
        text = " ".join([
            proposed.get("action", ""),
            proposed.get("type", ""),
            anonymized_prompt or "",
            str(anonymized_context or {}),
            str(payload.session_history or {}),
            payload.user_decision,
        ])
        return (await self.embed_text([text]))[0]

    async def embed_query(self, action: Any, ctx: dict, history: dict) -> List[float]:
        """Embed an action query for retrieval."""
        parts = [
            getattr(action.action, "value", str(action.action)),
            action.payload.get("type", ""),
            action.payload.get("name", ""),
            str(ctx),
            str(history),
        ]
        query_text = " ".join(parts)
        return (await self.embed_text([query_text]))[0]
