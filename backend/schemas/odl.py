"""Formal ODL Schema Definition - Enterprise Data Models

This module defines the comprehensive, formal data models for the Open Design Language (ODL).
These models form the authoritative single source of truth for all design operations,
with enterprise-grade validation, type safety, and architectural consistency.

Key architectural principles:
- Unified ODLGraph model with formal versioning and session management
- Consistent attribute access: node.data for component attributes, edge.attrs for connection metadata
- Port-aware architecture with terminal-level connection granularity
- Enhanced type safety with comprehensive Pydantic validation
- Standardized field naming: source_id/target_id with optional port specifications
- Enterprise features: requirements tracking, placeholder management, audit trails

This schema eliminates legacy inconsistencies and provides a robust foundation
for the entire electrical design automation platform.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal, Union
from datetime import datetime
import time

from pydantic import BaseModel, Field, ConfigDict, validator


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
    """A formal typed connection between two nodes in the design graph.

    This model defines connections using standardized source_id/target_id fields with
    optional port-level granularity. All edge metadata is stored in the attrs dictionary
    for consistency. The kind field categorizes connection types (electrical, mechanical, etc.).
    
    Key features:
    - Formal source_id/target_id naming (with backwards-compatible aliases)
    - Port-aware connections via source_port/target_port
    - Structured metadata in attrs dictionary
    - Connection categorization via kind field
    - Provisional marking for temporary connections
    """

    id: str
    # Primary fields using formal naming convention
    source_id: str = Field(..., alias="source")
    target_id: str = Field(..., alias="target") 
    # Port-level connection granularity
    source_port: Optional[str] = None
    target_port: Optional[str] = None
    # Structured edge metadata (replaces legacy 'data' field)
    attrs: Dict[str, Any] = Field(default_factory=dict)
    # Connection category for semantic understanding
    kind: Optional[str] = None  # e.g., "electrical", "mechanical", "data", "protection"
    # Provisional flag for temporary or suggested connections
    provisional: bool = False

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ODLGraph(BaseModel):
    """Formal unified graph model representing a complete electrical design.

    This is the authoritative data structure for all design operations, providing:
    - Session management with unique session_id
    - Optimistic concurrency control via version tracking
    - Structured node storage (Dict[str, ODLNode] keyed by node ID)
    - Ordered edge storage (List[ODLEdge] for connection sequences)
    - Embedded design requirements for holistic design context
    - Enterprise audit and metadata tracking

    The ODLGraph eliminates previous inconsistencies and provides a single,
    well-defined interface for all design manipulation operations.
    """

    session_id: str = Field(..., description="Unique session identifier")
    version: int = Field(default=1, ge=1, description="Graph version for optimistic concurrency")
    nodes: Dict[str, ODLNode] = Field(default_factory=dict, description="Component nodes keyed by ID")
    edges: List[ODLEdge] = Field(default_factory=list, description="Connection edges in sequence")
    requirements: Optional[DesignRequirements] = Field(None, description="Embedded design requirements")
    
    # Enterprise metadata
    created_at: Optional[float] = Field(default_factory=time.time, description="Creation timestamp")
    updated_at: Optional[float] = Field(default_factory=time.time, description="Last update timestamp")
    design_stage: str = Field(default="draft", description="Design stage: draft, review, approved, archived")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional graph metadata")

    model_config = ConfigDict(extra="forbid")

    def get_nodes_by_type(self, node_type: str) -> List[ODLNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.type == node_type]
    
    def get_edges_by_kind(self, kind: str) -> List[ODLEdge]:
        """Get all edges of a specific kind."""
        return [edge for edge in self.edges if edge.kind == kind]
    
    def get_node_connections(self, node_id: str) -> List[ODLEdge]:
        """Get all edges connected to a specific node."""
        return [edge for edge in self.edges 
                if edge.source_id == node_id or edge.target_id == node_id]
    
    def update_version(self) -> None:
        """Increment version and update timestamp for optimistic concurrency."""
        self.version += 1
        self.updated_at = time.time()


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

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# FORMAL GUIDANCE CONSTANTS AND ENUMERATIONS
# ============================================================================
# 
# These constants provide standardized values for the formal ODL schema.
# They are advisory for tools but enforce consistency across the platform.

# Standard port types for electrical connections
STANDARD_PORT_TYPES = {
    # DC electrical ports
    "dc_pos", "dc_neg", "dc+", "dc-",
    # AC electrical ports  
    "ac_l1", "ac_l2", "ac_l3", "ac_n", "ac_pe",
    # Grounding and safety
    "equipment_ground", "gnd", "earth", "pe",
    # Control and communication
    "comm_rx", "comm_tx", "rs485_a", "rs485_b",
    "can_h", "can_l", "modbus", "ethernet",
    # Monitoring and sensing
    "voltage_sense", "current_sense", "temp_sense",
    # Power optimizer and microinverter
    "pv_in", "ac_out", "data", "shutdown"
}

# Standard edge kinds for connection categorization
STANDARD_EDGE_KINDS = {
    # Electrical connections
    "electrical",           # Generic electrical connection
    "dc_string",           # DC string series connection
    "dc_parallel",         # DC parallel connection
    "ac_branch",           # AC branch circuit
    "ac_main",             # AC main panel connection
    "grounding",           # Equipment grounding connection
    "bonding",             # Electrical bonding connection
    
    # Protection and control
    "protection",          # Protection device integration
    "disconnect",          # Disconnect switch connection
    "monitoring",          # Monitoring system connection
    "control",             # Control signal connection
    
    # Communication and data
    "communication",       # Data/communication connection
    "rs485",              # RS485 communication bus
    "ethernet",           # Ethernet data connection
    "can_bus",            # CAN bus connection
    
    # Physical and mechanical
    "mechanical",         # Mechanical attachment/mounting
    "structural",         # Structural support connection
    "conduit",            # Conduit/raceway routing
    
    # Logical and planning
    "provisional",        # Temporary/planned connection
    "annotation",         # Annotation or documentation link
    "grouping"            # Logical grouping relationship
}

# Standard component types for node categorization
STANDARD_COMPONENT_TYPES = {
    # PV system components
    "panel", "pv_module", "solar_panel",
    "inverter", "string_inverter", "central_inverter", "microinverter",
    "power_optimizer", "optimizer", "mlpe",
    
    # Energy storage
    "battery", "battery_bank", "energy_storage",
    "charge_controller", "battery_inverter",
    
    # Electrical infrastructure  
    "main_panel", "load_center", "distribution_panel",
    "breaker", "fuse", "protection_device",
    "disconnect", "switch", "combiner_box",
    "transformer", "meter", "production_meter",
    
    # Monitoring and control
    "monitoring_device", "gateway", "data_logger",
    "rapid_shutdown", "safety_device",
    
    # Physical infrastructure
    "mounting_rail", "mounting_system", "racking",
    "conduit", "wire", "cable", "conductor",
    
    # Generic placeholders
    "generic_panel", "generic_inverter", "generic_battery",
    "generic_protection", "generic_disconnect", "generic_monitoring"
}

# Node layer classifications for UI rendering
STANDARD_NODE_LAYERS = {
    "single-line",        # Single-line electrical diagram
    "schematic",          # Detailed schematic view  
    "physical",           # Physical layout view
    "installation",       # Installation diagram
    "as-built"            # As-built documentation
}