# backend/schemas/component.py
"""Pydantic schemas for component operations."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ComponentBase(BaseModel):
    """Shared attributes for a component."""

    name: str
    type: str
    standard_code: str
    x: int = 100
    y: int = 100

    #: Name of the layer this component belongs to.  Defaults to
    #: "Single-Line Diagram".  Including the layer here allows clients
    #: to specify which canvas layer the component should appear on.
    layer: str = "Single-Line Diagram"


class ComponentCreate(ComponentBase):
    """Schema for creating a component."""

    pass


class Component(ComponentBase):
    """Schema returned from the API."""

    id: str

    #: Layer name from the database.  Mirrors the ComponentBase definition but
    #: is included here so Pydantic can serialise the ORM model including
    #: the ``layer`` column.
    layer: str

    model_config = ConfigDict(from_attributes=True)


class ComponentUpdate(BaseModel):
    """Schema for updating a component."""

    name: str | None = None
    type: str | None = None
    standard_code: str | None = None
    x: int | None = None
    y: int | None = None

    # Allow updating the layer of an existing component.  This field is
    # optional; if omitted, the layer remains unchanged.
    layer: str | None = None

    model_config = ConfigDict(extra="forbid")
