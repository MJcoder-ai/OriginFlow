"""Schemas for ODL graph operations."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ODLNode(BaseModel):
    id: str
    type: str
    data: Dict[str, Any] = {}
    layer: Optional[str] = None


class ODLEdge(BaseModel):
    source: str
    target: str
    data: Dict[str, Any] = {}


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
    card: Dict[str, Any]
    patch: Dict[str, Any] | None = None
    status: str
    version: int | None = None
    updated_tasks: List[Dict[str, Any]] | None = None
    next_recommended_task: str | None = None
    execution_time_ms: int | None = None


class VersionDiffResponse(BaseModel):
    """Response model for version difference queries."""
    from_version: int
    to_version: int
    changes: List[Dict[str, Any]]
    summary: str


class VersionRevertRequest(BaseModel):
    """Request model for version revert operations."""
    target_version: int


class VersionRevertResponse(BaseModel):
    """Response model for version revert operations."""
    success: bool
    message: str
    current_version: int
    graph_summary: str