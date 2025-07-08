# backend/schemas.py
"""Pydantic schemas for API validation.

Defines request and response models for FastAPI endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel

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

    class Config:
        from_attributes = True
