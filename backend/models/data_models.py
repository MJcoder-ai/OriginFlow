# backend/models/data_models.py
"""SQLAlchemy ORM models for the application.

Defines tables representing components and links between them.
"""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

class Component(Base):
    """Database model for a schematic component."""

    __tablename__ = "components"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    standard_code: Mapped[str] = mapped_column(String, unique=True)
    x: Mapped[int] = mapped_column(Integer, default=100)
    y: Mapped[int] = mapped_column(Integer, default=100)

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"Component(id={self.id!r}, name={self.name!r})"


class Link(Base):
    """Database model representing a connection between two components."""

    __tablename__ = "links"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    source_id: Mapped[str] = mapped_column(
        String, ForeignKey("components.id", ondelete="CASCADE")
    )
    target_id: Mapped[str] = mapped_column(
        String, ForeignKey("components.id", ondelete="CASCADE")
    )

    source: Mapped[Component] = relationship("Component", foreign_keys=[source_id])
    target: Mapped[Component] = relationship("Component", foreign_keys=[target_id])

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"Link(id={self.id!r}, source_id={self.source_id!r}, target_id={self.target_id!r})"

# Additional models such as Project will be added here in the future.
