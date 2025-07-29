# backend/models/link.py
"""ORM model representing a connection between components."""
from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models import Base
from backend.models.component import Component


class Link(Base):
    """Database model representing a connection between two components."""

    __tablename__ = "links"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    source_id: Mapped[str] = mapped_column(
        String, ForeignKey("schematic_components.id", ondelete="CASCADE")
    )
    target_id: Mapped[str] = mapped_column(
        String, ForeignKey("schematic_components.id", ondelete="CASCADE")
    )

    source: Mapped[Component] = relationship(Component, foreign_keys=[source_id])
    target: Mapped[Component] = relationship(Component, foreign_keys=[target_id])

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"Link(id={self.id!r}, source_id={self.source_id!r}, target_id={self.target_id!r})"
