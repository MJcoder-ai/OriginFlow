"""Pydantic schemas for ComponentMaster."""
from __future__ import annotations

from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


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

    # New fields for hierarchical modelling.  These correspond to
    # additional columns in ``component_master`` and enable the AI to
    # generate detailed wiring and sub-assemblies.
    ports: Optional[list] = Field(
        None,
        description=(
            "List of port definitions describing physical connection points on "
            "the component. Each entry may include a type (e.g. 'DC', 'AC', 'ground', 'data') "
            "and electrical limits. Enables detailed wiring in electrical layers."
        ),
    )
    dependencies: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Dependency rules specifying required, optional, and conflicting sub-components. "
            "For example, a panel may require mounting brackets and rails. Stored as JSON."
        ),
    )
    layer_affinity: Optional[list] = Field(
        None,
        description=(
            "List of layers (e.g. ['single-line','electrical','structural']) where this component naturally belongs."
        ),
    )

    sub_elements: Optional[list] = Field(
        None,
        description=(
            "Nested sub-components or accessories that form part of this component. "
            "Each entry should include its own part identifier and properties. "
            "This enables hierarchical assemblies (e.g. a PV panel with brackets and rails)."
        ),
    )


class ComponentMasterCreate(ComponentMasterBase):
    """Schema for creating a record."""

    pass


class ComponentMasterInDB(ComponentMasterBase):
    """Record stored in DB."""

    id: int

    model_config = ConfigDict(from_attributes=True)
