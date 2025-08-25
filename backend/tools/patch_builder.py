"""
Patch builder utility to provide a convenient interface for creating ODL patches.

This module provides a PatchBuilder class that matches the interface expected 
by PV tools, allowing them to call .add_node(), .set_meta(), etc. and then
converting to the proper ODLPatch format.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from uuid import uuid4
from backend.odl.schemas import ODLPatch, PatchOp
from backend.tools.schemas import make_patch


class PatchBuilder:
    """Helper class to build ODL patches with a convenient interface."""
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.operations: List[PatchOp] = []
        self._op_counter = 0
    
    def _next_op_id(self) -> str:
        """Generate unique operation ID."""
        self._op_counter += 1
        return f"{self.request_id}:op:{self._op_counter}"
    
    def add_node(self, kind: str, attrs: Optional[Dict[str, Any]] = None, layer: str = "single-line", node_id: Optional[str] = None) -> str:
        """Add a node to the patch."""
        if node_id is None:
            node_id = f"{kind}_{uuid4().hex[:8]}"
        
        op = PatchOp(
            op_id=self._next_op_id(),
            op="add_node",
            value={
                "id": node_id,
                "type": kind,
                "attrs": attrs or {}
            }
        )
        self.operations.append(op)
        return node_id
    
    def update_node(self, node_id: str, attrs: Dict[str, Any]) -> None:
        """Update node attributes."""
        op = PatchOp(
            op_id=self._next_op_id(),
            op="update_node",
            value={
                "id": node_id,
                "attrs": attrs
            }
        )
        self.operations.append(op)
    
    def add_edge(self, source_id: str, target_id: str, kind: str = "electrical", attrs: Optional[Dict[str, Any]] = None, edge_id: Optional[str] = None) -> str:
        """Add an edge to the patch."""
        if edge_id is None:
            edge_id = f"edge_{uuid4().hex[:8]}"
        
        op = PatchOp(
            op_id=self._next_op_id(),
            op="add_edge",
            value={
                "id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "kind": kind,
                "attrs": attrs or {}
            }
        )
        self.operations.append(op)
        return edge_id
    
    def set_meta(self, path: str, data: Any, merge: bool = False) -> None:
        """Set metadata in the patch."""
        op = PatchOp(
            op_id=self._next_op_id(),
            op="set_meta",
            value={
                "path": path,
                "data": data,
                "merge": merge
            }
        )
        self.operations.append(op)
    
    def to_patch(self) -> ODLPatch:
        """Convert to ODLPatch."""
        return make_patch(self.request_id, self.operations)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return self.to_patch().model_dump()


# Legacy compatibility - provide a factory function that matches the expected interface
def ODLPatch(patch_id: Optional[str] = None) -> PatchBuilder:
    """Legacy compatibility function to create a patch builder."""
    request_id = patch_id or f"legacy_{uuid4().hex[:8]}"
    return PatchBuilder(request_id)