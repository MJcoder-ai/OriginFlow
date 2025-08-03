from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class DesignVector(Base):
    """Embedding representing a stored design for similarity search."""

    __tablename__ = "design_vectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vector: Mapped[list] = mapped_column(JSON)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"DesignVector(id={self.id})"
