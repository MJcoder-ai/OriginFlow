from __future__ import annotations
"""
Layout engine (pluggable).

Goal:
 - Respect per-layer locks (never move locked nodes).
 - Provide a layered (left->right) placement for UNLOCKED nodes as a sane default.
 - Keep API small so we can swap to ELK/Dagre later without touching callers.
"""
from typing import Dict, List, Tuple, Set

from backend.schemas.analysis import DesignSnapshot, CanvasComponent

H_GAP = 180  # px between layers
V_GAP = 120  # px between nodes in a layer


def _graph(snapshot: DesignSnapshot) -> Tuple[Dict[str, CanvasComponent], Dict[str, Set[str]]]:
    nodes: Dict[str, CanvasComponent] = {c.id: c for c in snapshot.components}
    adj: Dict[str, Set[str]] = {c.id: set() for c in snapshot.components}
    for l in snapshot.links:
        adj.setdefault(l.source_id, set()).add(l.target_id)
    return nodes, adj


def _layer_nodes(nodes: Dict[str, CanvasComponent], adj: Dict[str, Set[str]]) -> List[List[str]]:
    indeg: Dict[str, int] = {nid: 0 for nid in nodes}
    for src, targets in adj.items():
        for t in targets:
            indeg[t] += 1
    q: List[str] = [nid for nid, d in indeg.items() if d == 0]
    layers: List[List[str]] = []
    visited: Set[str] = set()
    while q:
        layer: List[str] = []
        next_q: List[str] = []
        for nid in q:
            if nid in visited:
                continue
            visited.add(nid)
            layer.append(nid)
            for t in adj.get(nid, []):
                indeg[t] -= 1
                if indeg[t] == 0:
                    next_q.append(t)
        layers.append(layer)
        q = next_q
    # any remaining nodes (cycles) put in last layer
    remaining = [nid for nid in nodes if nid not in visited]
    if remaining:
        layers.append(remaining)
    return layers


def apply_layout(snapshot: DesignSnapshot, layer: str = "single_line") -> DesignSnapshot:
    """
    Assigns positions for UNLOCKED nodes only. Locked nodes keep their coordinates.
    Produces a simple, stable left->right layout by layers.
    NOTE: This is the 'builtin' fallback; ELK/Dagre are handled in layout_provider.py.
    """
    nodes, adj = _graph(snapshot)
    layers = _layer_nodes(nodes, adj)

    for li, layer_nodes in enumerate(layers):
        x = 100 + li * H_GAP
        y0 = 100
        for idx, nid in enumerate(layer_nodes):
            c = nodes[nid]
            locked = (c.locked_in_layers or {}).get(layer, False)
            if locked:
                continue
            y = y0 + idx * V_GAP
            c.layout = {**(c.layout or {}), layer: {"x": float(x), "y": float(y)}}
    return snapshot
