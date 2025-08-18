from __future__ import annotations
"""
Layout provider shim:
 - "elk": call an external ELK HTTP service to compute positions for UNLOCKED nodes.
 - "builtin": use the internal layered fallback.
 - "dagre": indicate that the client should perform layout (server returns 501).

All providers return a dict: { node_id: {"x": float, "y": float} } for a single layer.
"""
from typing import Dict, List
import httpx

from backend.config import LAYOUT_PROVIDER, LAYOUT_HTTP_URL
from backend.schemas.analysis import DesignSnapshot
from backend.services.layout_engine import apply_layout

DEFAULT_NODE_SIZE = (120.0, 72.0)  # width, height (can be refined per type)


def _unlocked_ids(snapshot: DesignSnapshot, layer: str) -> List[str]:
    ids: List[str] = []
    for c in snapshot.components:
        if not (c.locked_in_layers or {}).get(layer, False):
            ids.append(c.id)
    return ids


def _collect_positions(snapshot: DesignSnapshot, layer: str) -> Dict[str, Dict[str, float]]:
    pos: Dict[str, Dict[str, float]] = {}
    for c in snapshot.components:
        p = (c.layout or {}).get(layer)
        if p:
            pos[c.id] = {"x": float(p["x"]), "y": float(p["y"])}
    return pos


def _elk_graph(snapshot: DesignSnapshot, layer: str) -> dict:
    """
    Build an ELK graph JSON structure.
    - Locked nodes carry fixed x/y.
    - Unlocked nodes carry size hints only.
    """
    children = []
    for c in snapshot.components:
        locked = (c.locked_in_layers or {}).get(layer, False)
        node = {
            "id": c.id,
            "width": DEFAULT_NODE_SIZE[0],
            "height": DEFAULT_NODE_SIZE[1],
            "properties": {
                "org.eclipse.elk.portConstraints": "FIXED_ORDER",
                # Optional: tell layered algorithm to respect left->right flow
            },
        }
        if locked:
            pos = (c.layout or {}).get(layer)
            if pos:
                node["x"] = float(pos["x"])
                node["y"] = float(pos["y"])
                node["properties"]["org.eclipse.elk.fixed"] = True
        children.append(node)

    edges = []
    for l in snapshot.links:
        edges.append({
            "id": f"e_{l.source_id}_{l.target_id}",
            "sources": [l.source_id],
            "targets": [l.target_id],
        })

    graph = {
        "id": "root",
        "layoutOptions": {
            "elk.algorithm": "layered",
            "elk.direction": "RIGHT",
            "elk.spacing.nodeNode": "50",
            "elk.layered.spacing.nodeNodeBetweenLayers": "120",
            "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
        },
        "children": children,
        "edges": edges,
    }
    return graph


async def suggest_positions(snapshot: DesignSnapshot, layer: str = "single_line") -> Dict[str, Dict[str, float]]:
    """
    Return suggested positions for UNLOCKED nodes on the given layer.
    Does NOT mutate the snapshot; callers may merge/persist as needed.
    """
    provider = LAYOUT_PROVIDER
    if provider == "elk":
        if not LAYOUT_HTTP_URL:
            raise RuntimeError("ELK provider selected but LAYOUT_HTTP_URL is not configured.")
        graph = _elk_graph(snapshot, layer)
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(LAYOUT_HTTP_URL, json=graph)
            r.raise_for_status()
            laid_out = r.json()
        unlocked = set(_unlocked_ids(snapshot, layer))
        out: Dict[str, Dict[str, float]] = {}
        for child in laid_out.get("children", []):
            nid = child.get("id")
            if nid in unlocked:
                out[nid] = {"x": float(child.get("x", 0.0)), "y": float(child.get("y", 0.0))}
        return out

    if provider == "builtin":
        snap_copy = snapshot.model_copy(deep=True)
        snap_copy = apply_layout(snap_copy, layer=layer)
        positions = _collect_positions(snap_copy, layer)
        unlocked = set(_unlocked_ids(snapshot, layer))
        return {nid: pos for nid, pos in positions.items() if nid in unlocked}

    if provider == "dagre":
        raise NotImplementedError("dagre layout is handled client-side.")

    snap_copy = snapshot.model_copy(deep=True)
    snap_copy = apply_layout(snap_copy, layer=layer)
    positions = _collect_positions(snap_copy, layer)
    unlocked = set(_unlocked_ids(snapshot, layer))
    return {nid: pos for nid, pos in positions.items() if nid in unlocked}
