from __future__ import annotations
"""Pluggable orthogonal edge routing service.

Providers:
 - ``elk``: call an external ELK HTTP endpoint with ``edgeRouting=ORTHOGONAL``
 - ``builtin``: grid-based Manhattan router with obstacle avoidance
 - ``client``: routing handled in the browser via ``elkjs`` (server returns 501)
"""

from typing import Dict, List, Tuple

import httpx

from backend.config import EDGE_ROUTER_PROVIDER, LAYOUT_HTTP_URL
from backend.schemas.analysis import DesignSnapshot

PADDING = 18.0  # obstacle padding around nodes (px)
GRID = 12.0  # grid resolution for builtin router


def _obstacles(
    snapshot: DesignSnapshot, layer: str
) -> List[Tuple[float, float, float, float]]:
    """Return inflated node rectangles as (x0, y0, x1, y1)."""

    rects: List[Tuple[float, float, float, float]] = []
    for c in snapshot.components:
        pos = (c.layout or {}).get(layer)
        if not pos:
            continue
        w = getattr(c, "width", 120.0) or 120.0
        h = getattr(c, "height", 72.0) or 72.0
        x0 = pos["x"] - w / 2 - PADDING
        y0 = pos["y"] - h / 2 - PADDING
        x1 = pos["x"] + w / 2 + PADDING
        y1 = pos["y"] + h / 2 + PADDING
        rects.append((x0, y0, x1, y1))
    return rects


def _ports(
    snapshot: DesignSnapshot, layer: str, src_id: str, tgt_id: str
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Simple L->R ports: source right edge center, target left edge center."""

    src = next(c for c in snapshot.components if c.id == src_id)
    tgt = next(c for c in snapshot.components if c.id == tgt_id)
    sw = getattr(src, "width", 120.0) or 120.0
    tw = getattr(tgt, "width", 120.0) or 120.0
    sp = (src.layout[layer]["x"] + sw / 2, src.layout[layer]["y"])
    tp = (tgt.layout[layer]["x"] - tw / 2, tgt.layout[layer]["y"])
    return sp, tp


def _grid_snap(x: float) -> float:
    return round(x / GRID) * GRID


def _bfs_manhattan(
    start: Tuple[float, float],
    goal: Tuple[float, float],
    rects: List[Tuple[float, float, float, float]],
) -> List[Tuple[float, float]]:
    """Simple BFS on a coarse grid avoiding rectangular obstacles."""

    from collections import deque

    sx, sy = _grid_snap(start[0]), _grid_snap(start[1])
    gx, gy = _grid_snap(goal[0]), _grid_snap(goal[1])

    def blocked(x: float, y: float) -> bool:
        for x0, y0, x1, y1 in rects:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return True
        return False

    dirs = [(GRID, 0), (-GRID, 0), (0, GRID), (0, -GRID)]
    q = deque([(sx, sy)])
    parent: Dict[Tuple[float, float], Tuple[float, float] | None] = {(sx, sy): None}

    while q:
        x, y = q.popleft()
        if (x, y) == (gx, gy):
            break
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if (nx, ny) in parent or blocked(nx, ny):
                continue
            parent[(nx, ny)] = (x, y)
            q.append((nx, ny))

    path: List[Tuple[float, float]] = []
    cur = (gx, gy)
    if cur not in parent:
        return [(sx, sy), (gx, sy), (gx, gy)]

    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()

    pruned: List[Tuple[float, float]] = []
    for p in path:
        if not pruned:
            pruned.append(p)
        elif len(pruned) >= 2:
            x0, y0 = pruned[-2]
            x1, y1 = pruned[-1]
            x2, y2 = p
            if (x0 == x1 == x2) or (y0 == y1 == y2):
                pruned[-1] = p
            else:
                pruned.append(p)
        else:
            pruned.append(p)
    return pruned


async def route_edges(
    snapshot: DesignSnapshot, layer: str = "single_line"
) -> Dict[str, List[Dict[str, float]]]:
    """Route all unlocked links on ``layer`` and return waypoint mappings."""

    provider = EDGE_ROUTER_PROVIDER

    if provider == "elk":
        if not LAYOUT_HTTP_URL:
            raise RuntimeError(
                "ELK router selected but LAYOUT_HTTP_URL is not configured."
            )

        children = []
        for c in snapshot.components:
            pos = (c.layout or {}).get(layer)
            if not pos:
                continue
            node = {
                "id": c.id,
                "x": pos["x"],
                "y": pos["y"],
                "width": getattr(c, "width", 120.0) or 120.0,
                "height": getattr(c, "height", 72.0) or 72.0,
                "properties": {"org.eclipse.elk.fixed": True},
            }
            children.append(node)

        edges = []
        unlocked: List[str] = []
        for l in snapshot.links:
            if (l.locked_in_layers or {}).get(layer):
                continue
            eid = l.id or f"e_{l.source_id}_{l.target_id}"
            edges.append({"id": eid, "sources": [l.source_id], "targets": [l.target_id]})
            unlocked.append(eid)

        graph = {
            "id": "root",
            "layoutOptions": {
                "elk.algorithm": "layered",
                "elk.direction": "RIGHT",
                "elk.edgeRouting": "ORTHOGONAL",
                "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
            },
            "children": children,
            "edges": edges,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(LAYOUT_HTTP_URL, json=graph)
            r.raise_for_status()
            out = r.json()

        routes: Dict[str, List[Dict[str, float]]] = {}
        for e in out.get("edges", []):
            eid = e.get("id")
            if eid not in unlocked:
                continue
            sections = e.get("sections") or []
            pts: List[Dict[str, float]] = []
            for s in sections:
                start = s.get("startPoint")
                end = s.get("endPoint")
                bends = s.get("bendPoints") or []
                if start:
                    pts.append({"x": float(start["x"]), "y": float(start["y"])})
                for b in bends:
                    pts.append({"x": float(b["x"]), "y": float(b["y"])})
                if end:
                    pts.append({"x": float(end["x"]), "y": float(end["y"])})
            if pts:
                routes[eid] = pts
        return routes

    if provider == "client":  # pragma: no cover - client-only
        raise NotImplementedError("client-side edge routing")

    # Builtin Manhattan router
    rects = _obstacles(snapshot, layer)
    routes: Dict[str, List[Dict[str, float]]] = {}
    for l in snapshot.links:
        if (l.locked_in_layers or {}).get(layer):
            continue
        if not ((next(c for c in snapshot.components if c.id == l.source_id).layout or {}).get(layer)):
            continue
        if not ((next(c for c in snapshot.components if c.id == l.target_id).layout or {}).get(layer)):
            continue
        s, t = _ports(snapshot, layer, l.source_id, l.target_id)
        path = _bfs_manhattan(s, t, rects)
        routes[l.id or f"e_{l.source_id}_{l.target_id}"] = [
            {"x": float(x), "y": float(y)} for (x, y) in path
        ]
    return routes


__all__ = ["route_edges"]

