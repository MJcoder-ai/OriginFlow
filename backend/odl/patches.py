"""
Patch application with idempotency and optimistic concurrency (CAS).

This module contains pure functions that validate and apply ODLPatch operations
on an ODLGraph.  Side-effect free; persistence is handled by `store.py`.
"""
from __future__ import annotations

from typing import Dict, Tuple
from backend.odl.schemas import ODLGraph, ODLPatch, PatchOp, ODLNode, ODLEdge


class PatchError(ValueError):
    pass


def _apply_op(g: ODLGraph, op: PatchOp) -> None:
    v = op.value
    if op.op == "add_node":
        node = ODLNode(**v)
        if node.id in g.nodes:
            # Idempotent: if the node exists with the same content, accept; else error
            if g.nodes[node.id] != node:
                raise PatchError(f"Node '{node.id}' already exists with different data")
            return
        g.nodes[node.id] = node
        return

    if op.op == "update_node":
        node_id = str(v.get("id", ""))
        if node_id not in g.nodes:
            raise PatchError(f"Node '{node_id}' not found")
        # Shallow update of attrs/type/master link
        n = g.nodes[node_id].model_copy(deep=True)
        if "type" in v: n.type = str(v["type"])
        if "component_master_id" in v: n.component_master_id = v["component_master_id"] or None
        if "attrs" in v:
            # Merge attrs, delete with value=None
            for k, val in dict(v["attrs"]).items():
                if val is None:
                    n.attrs.pop(k, None)
                else:
                    n.attrs[k] = val
        g.nodes[node_id] = n
        return

    if op.op == "remove_node":
        node_id = str(v.get("id", ""))
        if node_id in g.nodes:
            # Remove also any edges touching node_id
            g.nodes.pop(node_id)
            g.edges = [e for e in g.edges if e.source_id != node_id and e.target_id != node_id]
        return

    if op.op == "add_edge":
        edge = ODLEdge(**v)
        # Idempotent: skip if same edge id exists with same content
        exists = next((e for e in g.edges if e.id == edge.id), None)
        if exists:
            if exists != edge:
                raise PatchError(f"Edge '{edge.id}' already exists with different data")
            return
        # Validate endpoints
        if edge.source_id not in g.nodes or edge.target_id not in g.nodes:
            raise PatchError("Edge endpoints must exist")
        g.edges.append(edge)
        return

    if op.op == "update_edge":
        edge_id = str(v.get("id", ""))
        idx = next((i for i, e in enumerate(g.edges) if e.id == edge_id), -1)
        if idx < 0:
            raise PatchError(f"Edge '{edge_id}' not found")
        e = g.edges[idx]
        new = e.model_copy(deep=True)
        if "kind" in v: new.kind = str(v["kind"])
        if "attrs" in v:
            for k, val in dict(v["attrs"]).items():
                if val is None:
                    new.attrs.pop(k, None)
                else:
                    new.attrs[k] = val
        g.edges[idx] = new
        return

    if op.op == "remove_edge":
        edge_id = str(v.get("id", ""))
        g.edges = [e for e in g.edges if e.id != edge_id]
        return

    if op.op == "set_meta":
        # Merge meta keys; delete key with value=None
        for k, val in dict(v).items():
            if val is None:
                g.meta.pop(k, None)
            else:
                g.meta[k] = val
        return

    raise PatchError(f"Unknown op '{op.op}'")


def apply_patch(graph: ODLGraph, patch: ODLPatch, applied_op_ids: Dict[str, bool]) -> Tuple[ODLGraph, Dict[str, bool]]:
    """
    Apply a patch to a graph producing a new graph instance.
    `applied_op_ids` is a set-like dict used to skip already applied op_ids (idempotency).
    """
    g = graph.model_copy(deep=True)
    for op in patch.operations:
        if applied_op_ids.get(op.op_id):
            continue  # idempotent re-apply → no-op
        _apply_op(g, op)
        applied_op_ids[op.op_id] = True
    # version increment is handled by the store
    return g, applied_op_ids
