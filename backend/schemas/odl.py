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


class CreateSessionResponse(BaseModel):
    session_id: str


class GraphResponse(BaseModel):
    card: Dict[str, Any]
    patch: Dict[str, Any] | None = None
    status: str
