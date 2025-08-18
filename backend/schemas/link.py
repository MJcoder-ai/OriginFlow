# backend/schemas/link.py
"""Pydantic schemas for link operations."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, List, Literal


class LinkBase(BaseModel):
    """Shared attributes for a link."""

    source_id: str
    target_id: str
    path_by_layer: Dict[
        Literal["single_line", "high_level", "civil", "networking", "physical"],
        List[Dict[str, float]],
    ] = Field(default_factory=dict)
    locked_in_layers: Dict[
        Literal["single_line", "high_level", "civil", "networking", "physical"],
        bool,
    ] = Field(default_factory=dict)


class LinkCreate(LinkBase):
    """Schema for creating a link."""

    pass


class Link(LinkBase):
    """Schema returned from the API for a link."""

    id: str

    model_config = ConfigDict(from_attributes=True)
