"""Pydantic schemas for ComponentMaster."""
from __future__ import annotations

from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class ComponentMasterBase(BaseModel):
    """Base fields shared by create/update."""

    part_number: str = Field(..., description="Manufacturer part number")
    name: str = Field(..., description="Component name")
    manufacturer: str = Field(..., description="Manufacturer")
    category: str = Field(..., description="Component category")
    description: Optional[str] = Field(None, description="Description")
    voltage: Optional[float] = Field(None, description="Nominal voltage")
    current: Optional[float] = Field(None, description="Nominal current")
    power: Optional[float] = Field(None, description="Power rating")
    specs: Optional[Dict[str, Any]] = Field(None, description="Extra specs")
    price: Optional[float] = Field(None, description="Unit price")
    availability: Optional[int] = Field(None, description="Quantity available")
    deprecated: bool = Field(False, description="Deprecated flag")


class ComponentMasterCreate(ComponentMasterBase):
    """Schema for creating a record."""

    pass


class ComponentMasterInDB(ComponentMasterBase):
    """Record stored in DB."""

    id: int

    class Config:
        orm_mode = True
