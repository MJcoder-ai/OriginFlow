from __future__ import annotations
"""
Auto-wiring planner and service.

The planner computes missing links based on simple domain rules and avoids
creating duplicates, making the operation idempotent.  The service layer
persists newly created links and invokes the orthogonal router.  It is
designed to degrade gracefully when optional repositories or services are
unavailable (e.g. in unit tests).
"""

from typing import List, Dict, Set, Tuple, Optional

from backend.schemas.analysis import DesignSnapshot, Link, CanvasComponent
from backend.services.odl_sync import rebuild_odl_for_session
from backend.services.edge_router import route_edges

try:  # pragma: no cover - repositories are optional
    from backend.repositories.links import LinkRepo  # type: ignore
    from backend.repositories.snapshots import SnapshotRepo  # type: ignore
except Exception:  # pragma: no cover
    LinkRepo = None  # type: ignore
    SnapshotRepo = None  # type: ignore


# Allowed edges between base component classes
ALLOWED_EDGES: Set[Tuple[str, str]] = {
    ("panel", "inverter"),
    ("battery", "inverter"),
    ("optimizer", "panel"),
    ("combiner", "inverter"),
    ("meter", "inverter"),
}


def _base_class_of(t: str) -> str:
    t = (t or "").lower()
    if "panel" in t or "module" in t:
        return "panel"
    if "inverter" in t:
        return "inverter"
    if "battery" in t:
        return "battery"
    if "meter" in t:
        return "meter"
    if "optimizer" in t:
        return "optimizer"
    if "combiner" in t:
        return "combiner"
    return "other"


def _existing_pairs(snapshot: DesignSnapshot) -> Set[Tuple[str, str]]:
    return {(l.source_id, l.target_id) for l in snapshot.links}


def _group_by_class(snapshot: DesignSnapshot) -> Dict[str, List[CanvasComponent]]:
    groups: Dict[str, List[CanvasComponent]] = {}
    for c in snapshot.components:
        groups.setdefault(_base_class_of(c.type), []).append(c)
    return groups


def plan_missing_wiring(snapshot: DesignSnapshot) -> List[Tuple[str, str]]:
    """Plan a minimal set of missing links.

    The current implementation connects each panel and battery to its nearest
    inverter.  Only links permitted by ``ALLOWED_EDGES`` are considered.
    """

    pairs: List[Tuple[str, str]] = []
    existing = _existing_pairs(snapshot)
    groups = _group_by_class(snapshot)
    inverters = groups.get("inverter", [])
    if not inverters:
        return pairs

    def nearest_inverter(comp: CanvasComponent) -> Optional[CanvasComponent]:
        if not comp.layout:
            return inverters[0]
        layer = "single_line"
        cx = comp.layout.get(layer, {}).get("x", 0.0)
        cy = comp.layout.get(layer, {}).get("y", 0.0)
        best, bestd = None, 1e18
        for inv in inverters:
            ix = inv.layout.get(layer, {}).get("x", 0.0)
            iy = inv.layout.get(layer, {}).get("y", 0.0)
            d = (ix - cx) ** 2 + (iy - cy) ** 2
            if d < bestd:
                best, bestd = inv, d
        return best

    for p in groups.get("panel", []):
        inv = nearest_inverter(p)
        if not inv:
            continue
        pair = (p.id, inv.id)
        if pair not in existing and ("panel", "inverter") in ALLOWED_EDGES:
            pairs.append(pair)

    for b in groups.get("battery", []):
        inv = nearest_inverter(b)
        if not inv:
            continue
        pair = (b.id, inv.id)
        if pair not in existing and ("battery", "inverter") in ALLOWED_EDGES:
            pairs.append(pair)

    return pairs


class AutoWiringService:
    """Create missing links and run the edge router."""

    def __init__(self) -> None:  # pragma: no cover - optional repos
        self.link_repo = LinkRepo() if LinkRepo else None  # type: ignore
        self.snap_repo = SnapshotRepo() if SnapshotRepo else None  # type: ignore

    async def wire_missing_and_route(
        self, session_id: str, layer: str = "single_line"
    ) -> Dict[str, int]:
        if self.snap_repo is None or self.link_repo is None:
            return {"created_links": 0, "routed": 0}

        snapshot: Optional[DesignSnapshot] = await self.snap_repo.get_latest_snapshot(  # type: ignore
            session_id
        )
        if snapshot is None:
            return {"created_links": 0, "routed": 0}

        plan = plan_missing_wiring(snapshot)
        created = 0
        for src, tgt in plan:
            link = Link(source_id=src, target_id=tgt)
            await self.link_repo.create_link_for_session(session_id, link)  # type: ignore
            created += 1

        snapshot = await self.snap_repo.get_latest_snapshot(session_id)  # type: ignore
        if snapshot is None:
            return {"created_links": created, "routed": 0}

        routes = await route_edges(snapshot, layer=layer)
        for l in snapshot.links:
            eid = l.id or f"e_{l.source_id}_{l.target_id}"
            if eid in routes:
                l.path_by_layer[layer] = routes[eid]
                await self.link_repo.save_link(l)  # type: ignore
        await rebuild_odl_for_session(session_id)
        return {"created_links": created, "routed": len(routes)}


__all__ = ["plan_missing_wiring", "AutoWiringService"]

