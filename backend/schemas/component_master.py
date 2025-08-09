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

    # Series and variants support.  Many datasheets describe multiple product
    # variants (e.g. different wattages or options) under a common series.  The
    # ``series_name`` field stores the family identifier while ``variants`` holds
    # a list of per-variant attribute dictionaries extracted from the datasheet.
    # Each variant may include its own part number, power, voltage, dimensions
    # and other specifications.  These fields are optional and may be omitted
    # when a datasheet covers a single product.
    series_name: Optional[str] = Field(
        None,
        description=(
            "Name of the product series or family. A single datasheet may cover multiple "
            "variants under a common series (e.g. a panel model available in 400\u202fW, 420\u202fW and 450\u202fW)."
        ),
    )
    variants: Optional[list] = Field(
        None,
        description=(
            "List of variant definitions extracted from a multi-product datasheet. "
            "Each entry should include its own attributes such as part_number, power and voltage. "
            "This field is optional and may be empty for single-product datasheets."
        ),
    )


class ComponentMasterCreate(ComponentMasterBase):
    """Schema for creating a record."""

    pass


class ComponentMasterInDB(ComponentMasterBase):
    """Record stored in DB."""

    id: int

    model_config = ConfigDict(from_attributes=True)
