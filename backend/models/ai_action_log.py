"""ORM model for logging AI suggestions and user feedback.

The ``AiActionLog`` table records every AI-generated action along with the
user's decision (approve/reject/auto).  This enables the learning
subsystem to train confidence models on real usage patterns without
polluting the core schematic tables.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class AiActionLog(Base):
    """Persistent log of AI actions and user feedback."""

    __tablename__ = "ai_action_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_action: Mapped[dict] = mapped_column(JSON, nullable=False)
    user_decision: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AiActionLog(id={self.id}, session_id={self.session_id}, "
            f"decision={self.user_decision})"
        )
