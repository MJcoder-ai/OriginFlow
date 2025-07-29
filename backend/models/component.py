# backend/models/component.py
"""ORM model representing a schematic component."""
from __future__ import annotations

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class Component(Base):
    """Database model for a schematic component."""

    __tablename__ = "schematic_components"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    standard_code: Mapped[str] = mapped_column(String, unique=True)
    x: Mapped[int] = mapped_column(Integer, default=100)
    y: Mapped[int] = mapped_column(Integer, default=100)

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"Component(id={self.id!r}, name={self.name!r})"

