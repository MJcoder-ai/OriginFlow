from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class CanvasComponent(BaseModel):
    """Represents a component drawn on the design canvas.

    ``standard_code`` is optional in development: placeholder components
    (e.g. ``generic_panel``, ``generic_inverter``) do not have a code until
    they are replaced by a real part. Clients may omit this field or provide
    an empty string.

    The coordinates ``x`` and ``y`` describe the position on the canvas.
    Historically these were integers because the UI snapped components to a
    grid; however fractional positions are now supported. Both integers and
    floating-point numbers are accepted and will be coerced to floats during
    validation.
    """

    id: str
    name: str
    type: str
    # standard_code may be None for placeholder components
    standard_code: Optional[str] = None
    # Accept int or float for coordinates
    x: Union[int, float]
    y: Union[int, float]
    locked_in_layers: Optional[Dict[str, bool]] = None
    layout: Optional[Dict[str, Dict[str, float]]] = None

    @field_validator("x", "y", mode="before")
    def _coerce_numeric(cls, v: Any) -> float:
        """Ensure x/y are numeric and cast them to float.

        Raises:
            ValueError: if the value cannot be interpreted as a number.
        """
        if isinstance(v, (int, float)):
            return float(v)
        # Allow numeric strings to be converted
        try:
            return float(v)
        except Exception as exc:
            raise ValueError("coordinate must be numeric") from exc


class CanvasLink(BaseModel):
    id: str
    source_id: str
    target_id: str


class LayerSnapshot(BaseModel):
    """Represents a layer-specific view of the design."""

    name: str
    nodes: List[CanvasComponent] = Field(default_factory=list)
    links: List[CanvasLink] = Field(default_factory=list)


class DesignSnapshot(BaseModel):
    """A snapshot of a design session at a specific point in time."""

    id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None
    version: int = 1
    domain: Optional[str] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)
    components: List[CanvasComponent]
    links: List[CanvasLink]
    layers: Dict[str, LayerSnapshot] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


DesignSnapshot.model_rebuild()
