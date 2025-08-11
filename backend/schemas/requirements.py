"""Pydantic schemas for requirements updates."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RequirementsUpdate(BaseModel):
    """User‑supplied design requirements."""

    target_power: Optional[float] = Field(
        None, description="Desired array power in watts (e.g. 5000 for 5 kW)"
    )
    roof_area: Optional[float] = Field(
        None, description="Available roof area in square metres"
    )
    budget: Optional[float] = Field(None, description="Budget in currency units")
    brand: Optional[str] = Field(None, description="Preferred manufacturer brand")
