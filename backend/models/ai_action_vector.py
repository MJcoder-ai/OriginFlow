"""SQLAlchemy model for enriched AI action vectors.

This model extends the existing feedback logging system by storing
anonymized user prompts, design contexts, session history and
embedding vectors.  Each record corresponds to an AI action
submission and its approval outcome.  Embeddings are stored as
JSON lists of floats (optionally encrypted) and a metadata field
allows for arbitrary additional information.  See
``backend/services/embedding_service.py`` for how embeddings are
produced and ``backend/services/vector_store.py`` for how they are
persisted in a vector database.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import JSON, DateTime, String, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class AiActionVector(Base):
    """ORM model for enriched AI action vector records."""

    __tablename__ = "ai_action_vectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    component_type: Mapped[str | None] = mapped_column(String, nullable=True)
    user_prompt: Mapped[str] = mapped_column(String, nullable=False)
    anonymized_prompt: Mapped[str] = mapped_column(String, nullable=False)
    design_context: Mapped[dict] = mapped_column(JSON, nullable=True)
    anonymized_context: Mapped[dict] = mapped_column(JSON, nullable=True)
    session_history: Mapped[dict] = mapped_column(JSON, nullable=True)
    approval: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_shown: Mapped[float | None] = mapped_column(Float, nullable=True)
    confirmed_by: Mapped[str] = mapped_column(String, nullable=False, default="human")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    embedding: Mapped[list] = mapped_column(JSON, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"AiActionVector(id={self.id}, action_type={self.action_type}, "
            f"component_type={self.component_type}, approval={self.approval})"
        )
