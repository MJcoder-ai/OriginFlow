"""Schemas for ODL graph operations."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class ODLNode(BaseModel):
    id: str
    type: str
    data: Dict[str, Any] = {}
    layer: Optional[str] = None
    # NEW FIELDS for placeholder support
    placeholder: bool = False
    candidate_components: List[str] = []
    confidence_score: Optional[float] = None
    replacement_history: List[Dict[str, Any]] = []


class ODLEdge(BaseModel):
    source: str
    target: str
    data: Dict[str, Any] = {}
    # NEW FIELDS for enhanced connections
    connection_type: Optional[str] = None
    provisional: bool = False


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
    """Placeholder component definition."""
    type: str
    default_attributes: Dict[str, Any]
    replacement_categories: List[str]
    sizing_rules: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None


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