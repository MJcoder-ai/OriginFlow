# backend/schemas/link.py
"""Pydantic schemas for link operations."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LinkBase(BaseModel):
    """Shared attributes for a link."""

    source_id: str
    target_id: str


class LinkCreate(LinkBase):
    """Schema for creating a link."""

    pass


class Link(LinkBase):
    """Schema returned from the API for a link."""

    id: str

    model_config = ConfigDict(from_attributes=True)
