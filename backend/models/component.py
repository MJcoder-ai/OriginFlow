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

    #: Name of the layer this component belongs to.  Added in Phase 2 to
    #: support multiple canvas layers (e.g., "Single-Line Diagram",
    #: "High-Level Overview"). Defaults to "Single-Line Diagram" when
    #: not specified.  Persisting this field allows the frontend to
    #: restore components to the correct layer when reloading a project.
    layer: Mapped[str] = mapped_column(String, default="Single-Line Diagram")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"Component(id={self.id!r}, name={self.name!r})"

