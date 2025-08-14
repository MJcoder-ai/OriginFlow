"""Standard output envelope model.

Agent templates and the orchestrator exchange data using a standard
envelope structure.  The envelope provides a consistent set of
fields for status reporting, results, patches to the ODL graph,
cards (for metadata such as confidence), metrics, validation
messages, errors and recommended next actions.  Using a Pydantic
model ensures that these structures are type-checked and easily
validated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StandardEnvelope(BaseModel):
    """Schema for agent outputs and orchestrator responses."""

    status: str = Field(..., description="Overall outcome (complete, error, etc.)")
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Primary data payload produced by the agent"
    )
    patch: Optional[Dict[str, Any]] = Field(
        default=None, description="Graph patch describing modifications to the ODL graph"
    )
    card: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata about the operation, e.g. confidence scores"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Telemetry metrics collected during execution"
    )
    validations: List[str] = Field(
        default_factory=list, description="Messages from schema validation or rule checking"
    )
    errors: List[str] = Field(
        default_factory=list, description="Descriptions of errors encountered"
    )
    next_actions: List[str] = Field(
        default_factory=list, description="Suggested next actions or follow-up tasks"
    )
