"""
ODL (Open Design Language) core schemas.

These Pydantic models define the **single source of truth** for a design
session.  All canvases and views must be derived projections of ODL state.

Versioning:
- The store assigns a monotonically increasing integer `version` per session.
  All `PATCH` applications require optimistic concurrency via `If-Match`.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class ODLNode(BaseModel):
    """A node in the design graph."""
    id: str
    type: str  # e.g., "panel", "inverter", "battery", "mount", "wire", etc.
    component_master_id: Optional[str] = None  # stable link to parts library
    attrs: Dict[str, object] = Field(default_factory=dict)  # arbitrary structured metadata
    model_config = ConfigDict(extra="forbid")


class ODLEdge(BaseModel):
    """A typed connection between two nodes."""
    id: str
    source_id: str
    target_id: str
    kind: str  # e.g., "electrical", "mechanical", "data"
    attrs: Dict[str, object] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid")


class ODLGraph(BaseModel):
    """The full design graph for a session."""
    session_id: str
    version: int
    nodes: Dict[str, ODLNode] = Field(default_factory=dict)
    edges: List[ODLEdge] = Field(default_factory=list)
    meta: Dict[str, object] = Field(default_factory=dict)  # requirements, domain, etc.
    model_config = ConfigDict(extra="forbid")


class PatchOp(BaseModel):
    """Single patch operation (idempotent by `op_id`)."""
    op_id: str  # idempotency key for this op
    op: Literal[
        "add_node", "update_node", "remove_node",
        "add_edge", "update_edge", "remove_edge",
        "set_meta"
    ]
    value: Dict[str, object] = Field(default_factory=dict)  # op-specific payload
    model_config = ConfigDict(extra="forbid")


class ODLPatch(BaseModel):
    """A set of operations to apply atomically to an ODLGraph."""
    patch_id: str  # idempotency key for whole patch
    operations: List[PatchOp]
    model_config = ConfigDict(extra="forbid")


class LayerView(BaseModel):
    """A projection for rendering (e.g., single-line, electrical, structural)."""
    session_id: str
    base_version: int
    layer: str
    nodes: List[ODLNode]
    edges: List[ODLEdge]
    model_config = ConfigDict(extra="forbid")


# --- OriginFlow guidance enums (non-breaking; tools may adopt these) ---
# These constants are advisory; existing graphs remain valid without them.
PORT_TYPES = {
    "dc+", "dc-", "ac_L1", "ac_L2", "ac_L3", "ac_N", "pe",
    "ctl", "comm_rx", "comm_tx", "shield",
}

EDGE_KINDS = {
    "dc_string", "dc_bus",
    "ac_branch", "ac_feeder", "egc",
    "comm",
    "mechanical",          # mounted_on / attached_to relationships
    "route",               # path segments / goes_through
    "bundle",              # conductor set between devices for BOM/routing
    "protection",
    "annotation",
}

# Meta paths commonly used by tools:
#   meta.design_state
#   meta.physical.bundles / routes / schedules
#   meta.mechanical.surfaces / loads
# These are not enforced here to keep ODL generic; tools use them consistently.
