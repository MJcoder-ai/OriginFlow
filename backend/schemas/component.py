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


class ComponentCreate(ComponentBase):
    """Schema for creating a component."""

    pass


class Component(ComponentBase):
    """Schema returned from the API."""

    id: str

    model_config = ConfigDict(from_attributes=True)


class ComponentUpdate(BaseModel):
    """Schema for updating a component."""

    name: str | None = None
    type: str | None = None
    standard_code: str | None = None
    x: int | None = None
    y: int | None = None

    model_config = ConfigDict(extra="forbid")
