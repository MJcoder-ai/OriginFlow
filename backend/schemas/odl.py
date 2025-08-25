"""Schemas for ODL graph operations.

This module defines the core data models for the Open Design Language (ODL).
The models here form the single source of truth for design sessions. They have
been extended to support port-level connections so that tools can operate on
individual terminals rather than whole devices.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ODLNode(BaseModel):
    """A node in the design graph.

    Each node represents a physical component, placeholder or logical entity. In
    addition to generic metadata, nodes can now carry a map of ports. Each
    port entry describes a terminal available for wiring with keys like
    `type` (e.g. "dc+", "ac_L1"), `direction` (input/output), and
    `max_connections`. Tools should not remove or reorder ports once created
    because edges refer to them by name.
    """

    id: str
    type: str  # e.g., "panel", "inverter", "battery", "mount", "wire", etc.
    data: Dict[str, Any] = Field(default_factory=dict)
    layer: Optional[str] = None
    # Port dictionary keyed by a stable port identifier. Each value is a
    # dictionary describing the port.
    ports: Optional[Dict[str, Dict[str, Any]]] = None
    # Placeholder support metadata
    placeholder: bool = False
    candidate_components: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    replacement_history: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ODLEdge(BaseModel):
    """A typed connection between two nodes.

    Edges now reference specific ports on the source and target nodes. If
    unspecified, the connection is assumed to be at the device level (for
    backwards compatibility). The ``connection_type`` can be used to denote
    whether this is a DC string, AC branch, data communication, etc.
    """

    id: str
    source: str
    target: str
    source_port: Optional[str] = None  # stable port identifier on source node
    target_port: Optional[str] = None  # stable port identifier on target node
    data: Dict[str, Any] = Field(default_factory=dict)
    connection_type: Optional[str] = None
    provisional: bool = False

    model_config = ConfigDict(extra="forbid")


class DesignRequirements(BaseModel):
    """Design requirements embedded in ODL graph."""
    target_power: Optional[float] = Field(None, description="Target power in Watts")
    roof_area: Optional[float] = Field(None, description="Available roof area in square meters")
    budget: Optional[float] = Field(None, description="Budget in dollars")
    preferred_brands: List[str] = Field(default_factory=list, description="Preferred component brands")
    backup_hours: Optional[float] = Field(None, description="Required backup power hours")
    load_profile: Optional[Dict[str, Any]] = Field(None, description="Load profile data")
    environmental_conditions: Optional[Dict[str, Any]] = Field(None, description="Environmental conditions")
    
    # Computed fields (set by planner)
    estimated_panel_count: Optional[int] = None
    estimated_inverter_count: Optional[int] = None
    estimated_battery_count: Optional[int] = None
    estimated_total_cost: Optional[float] = None
    
    # Metadata
    last_updated: Optional[str] = None
    completion_status: float = Field(default=0.0, description="Requirements completion percentage")


class ComponentCandidate(BaseModel):
    """Candidate component for replacing placeholders."""
    part_number: str
    name: str
    category: str
    power: Optional[float] = None
    price: Optional[float] = None
    manufacturer: Optional[str] = None
    efficiency: Optional[float] = None
    suitability_score: float = 0.0
    availability: bool = True
    metadata: Dict[str, Any] = {}


class PlaceholderComponent(BaseModel):
    """Placeholder component definition with port support."""
    type: str
    default_attributes: Dict[str, Any]
    replacement_categories: List[str]
    sizing_rules: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    ports: Optional[List[Dict[str, Any]]] = None  # Port templates for this component type

    model_config = ConfigDict(extra="forbid")


class GraphPatch(BaseModel):
    add_nodes: List[ODLNode] | None = None
    add_edges: List[ODLEdge] | None = None
    remove_nodes: List[str] | None = None
    remove_edges: List[Dict[str, str]] | None = None


class ActOnTaskRequest(BaseModel):
    task_id: str
    # Optional action variant for tasks that expose sub-operations
    action: str | None = None
    # Client-observed graph version for optimistic concurrency control
    graph_version: int | None = None


class CreateSessionResponse(BaseModel):
    session_id: str


class CreateSessionRequest(BaseModel):
    session_id: str | None = None


class GraphResponse(BaseModel):
    card: Dict[str, Any]
    patch: Dict[str, Any] | None = None
    status: str
    version: int | None = None


class RequirementsStatusResponse(BaseModel):
    """Response model for requirements status endpoint."""
    missing_requirements: List[str]
    missing_components: List[str]
    requirements_complete: bool
    components_available: bool
    can_proceed: bool
    graph_summary: str


class DesignCardAction(BaseModel):
    """Interactive action for design cards."""
    label: str
    command: str
    variant: Optional[str] = None
    enabled: bool = True
    icon: Optional[str] = None


class DesignCardSpec(BaseModel):
    """Specification detail for design cards."""
    label: str
    value: str
    unit: Optional[str] = None
    confidence: Optional[float] = None


class DesignCard(BaseModel):
    """Enhanced design card with confidence and interactive actions."""
    title: str
    body: str
    confidence: Optional[float] = None
    specs: List[DesignCardSpec] = []
    actions: List[DesignCardAction] = []
    warnings: List[str] = []
    recommendations: List[str] = []


class TaskExecutionResponse(BaseModel):
    """Enhanced response model for task execution with status updates."""
    card: DesignCard
    patch: Optional[Dict[str, Any]] = None
    status: str = Field(..., pattern="^(pending|in_progress|complete|blocked)$")
    version: Optional[int] = None
    updated_tasks: Optional[List[Dict[str, Any]]] = None
    next_recommended_task: Optional[str] = None
    execution_time_ms: Optional[int] = Field(None, ge=0)


class VersionDiffResponse(BaseModel):
    """Response model for version difference queries."""
    from_version: int = Field(..., ge=1)
    to_version: int = Field(..., ge=1)
    changes: List[Dict[str, Any]]
    summary: str


class VersionRevertRequest(BaseModel):
    """Request model for version revert operations."""
    target_version: int = Field(..., ge=1)


class VersionRevertResponse(BaseModel):
    """Response model for version revert operations."""
    success: bool
    message: str
    current_version: int
    graph_summary: str


class ComponentSelectionRequest(BaseModel):
    """Request for selecting a real component to replace placeholder."""
    placeholder_id: str
    component: ComponentCandidate
    apply_to_all_similar: bool = False


class ComponentSelectionResponse(BaseModel):
    """Response for component selection operations."""
    success: bool
    message: str
    replaced_nodes: List[str]
    patch: Dict[str, Any]
    updated_design_summary: str


class RequirementsUpdateRequest(BaseModel):
    """Request for updating design requirements."""
    requirements: DesignRequirements


class RequirementsUpdateResponse(BaseModel):
    """Response for requirements update operations."""
    success: bool
    message: str
    updated_requirements: DesignRequirements
    affected_tasks: List[str]


class ODLTextResponse(BaseModel):
    """Response containing ODL text representation."""
    text: str
    version: int
    last_updated: Optional[str] = None
    node_count: int
    edge_count: int


class PlaceholderAnalysisResponse(BaseModel):
    """Response containing placeholder analysis."""
    total_placeholders: int
    placeholders_by_type: Dict[str, int]
    available_replacements: Dict[str, List[ComponentCandidate]]
    completion_percentage: float
    blocking_issues: List[str]