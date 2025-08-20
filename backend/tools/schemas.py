"""
Typed schemas for tool inputs/outputs.

Tools are **pure**: they take typed inputs (small ODL slices + params) and
return typed outputs (usually an ODLPatch). They never talk to the DB or the
ODL store directly. The orchestrator composes tools and applies returned
patches via the ODL API.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from backend.odl.schemas import ODLNode, ODLEdge, ODLGraph, ODLPatch, PatchOp


# ---------- Shared ----------


class ToolBase(BaseModel):
    """Base fields common to tool requests."""

    session_id: str = Field(..., description="Design session id")
    request_id: str = Field(..., description="Idempotency scope for op_ids")
    model_config = ConfigDict(extra="forbid")


# ---------- Selection ----------


class ComponentCandidate(BaseModel):
    part_number: str
    name: str
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    power: Optional[float] = None
    price: Optional[float] = None
    score: Optional[float] = Field(None, description="Ranking score (higher is better)")


class SelectionInput(ToolBase):
    placeholder_type: str = Field(
        ..., description="e.g., generic_panel, generic_inverter"
    )
    requirements: Dict[str, float] = Field(
        default_factory=dict, description="Structured requirements (e.g., target_power)"
    )
    pool: List[Dict] = Field(
        default_factory=list, description="Candidate component dicts from library"
    )


class SelectionResult(BaseModel):
    candidates: List[ComponentCandidate]


# ---------- Wiring ----------


class GenerateWiringInput(ToolBase):
    view_nodes: List[ODLNode] = Field(
        default_factory=list, description="Nodes visible in the current layer/view"
    )
    edge_kind: str = Field("electrical")


# ---------- Structural ----------


class GenerateMountsInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    mount_type: str = Field("mount")
    layer: str = Field("structural")


# ---------- Monitoring ----------


class AddMonitoringInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    device_type: str = Field("monitoring")
    layer: str = Field("electrical")


# ---------- Placeholders ----------


class MakePlaceholdersInput(ToolBase):
    count: int = Field(1, ge=1)
    placeholder_type: str = Field(
        ..., description="generic_panel | generic_inverter | ..."
    )
    attrs: Dict[str, object] = Field(default_factory=dict)


# ---------- Consensus ----------


class RankInput(BaseModel):
    candidates: List[ComponentCandidate]
    objective: Literal["max_score", "min_price", "best_value"] = "max_score"


class RankResult(BaseModel):
    candidates: List[ComponentCandidate]


# ---------- Helpers ----------


def make_patch(request_id: str, ops: List[PatchOp]) -> ODLPatch:
    """Create an ODLPatch with a deterministic patch_id from request_id."""

    return ODLPatch(patch_id=f"patch:{request_id}", operations=ops)
