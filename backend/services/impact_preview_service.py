from __future__ import annotations

"""Lightweight graph diff + pending action preview service.

This module provides two helpers:
* :class:`SnapshotDiffService` – compute a structural diff between two
  simple ``{"nodes": [...], "edges": [...]}`` graphs.
* :class:`ImpactPreviewService` – given a ``PendingAction`` record,
  attempt to simulate its effect on the latest design snapshot and
  produce a diff.  The simulation is intentionally conservative and
  schema‑agnostic so that it never mutates real data and fails soft
  when faced with unknown action types.

The service is designed to be self‑contained so that other parts of the
codebase can be refactored independently.
"""

from copy import deepcopy
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Snapshot model import – repository may not yet have snapshots; fall back
# gracefully so the service can still be imported without errors.
try:  # pragma: no cover - import resolution
    from backend.models.design_snapshot import DesignSnapshot  # type: ignore
except Exception:  # pragma: no cover - import resolution
    try:
        from backend.models.snapshots import DesignSnapshot  # type: ignore
    except Exception:  # pragma: no cover - import resolution
        DesignSnapshot = None  # type: ignore

from backend.models.pending_action import PendingAction

Graph = Dict[str, Any]


class SnapshotDiffService:
    """Compute a shallow diff between two graphs."""

    @staticmethod
    def _index_nodes(g: Graph) -> Dict[str, Dict[str, Any]]:
        nodes = g.get("nodes") or []
        out: Dict[str, Dict[str, Any]] = {}
        for n in nodes:
            nid = str(n.get("id"))
            if nid:
                out[nid] = n
        return out

    @staticmethod
    def _edge_key(e: Dict[str, Any]) -> Tuple[str, str, str]:
        return (
            str(e.get("source")),
            str(e.get("target")),
            str(e.get("type") or e.get("kind") or ""),
        )

    @staticmethod
    def _index_edges(g: Graph) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
        edges = g.get("edges") or g.get("links") or []
        out: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        for e in edges:
            out[SnapshotDiffService._edge_key(e)] = e
        return out

    @staticmethod
    def compute(before: Graph, after: Graph) -> Dict[str, Any]:
        b_nodes = SnapshotDiffService._index_nodes(before)
        a_nodes = SnapshotDiffService._index_nodes(after)
        b_edges = SnapshotDiffService._index_edges(before)
        a_edges = SnapshotDiffService._index_edges(after)

        added_nodes = []
        removed_nodes = []
        modified_nodes = []
        for nid, n in a_nodes.items():
            if nid not in b_nodes:
                added_nodes.append(
                    {"id": nid, "name": n.get("name"), "type": n.get("type")}
                )
            else:
                b = b_nodes[nid]
                changes = {}
                # shallow compare common scalar fields
                for k in set(list(n.keys()) + list(b.keys())):
                    if k in {"id"}:
                        continue
                    v1, v0 = n.get(k), b.get(k)
                    if (
                        isinstance(v1, (str, int, float, bool, type(None)))
                        and isinstance(v0, (str, int, float, bool, type(None)))
                        and v1 != v0
                    ):
                        changes[k] = {"before": v0, "after": v1}
                if changes:
                    modified_nodes.append({"id": nid, "changes": changes})
        for nid, n in b_nodes.items():
            if nid not in a_nodes:
                removed_nodes.append(
                    {"id": nid, "name": n.get("name"), "type": n.get("type")}
                )

        added_edges = []
        removed_edges = []
        for k, e in a_edges.items():
            if k not in b_edges:
                added_edges.append(
                    {
                        "source": e.get("source"),
                        "target": e.get("target"),
                        "type": e.get("type") or e.get("kind"),
                    }
                )
        for k, e in b_edges.items():
            if k not in a_edges:
                removed_edges.append(
                    {
                        "source": e.get("source"),
                        "target": e.get("target"),
                        "type": e.get("type") or e.get("kind"),
                    }
                )

        return {
            "added_nodes": added_nodes,
            "removed_nodes": removed_nodes,
            "modified_nodes": modified_nodes,
            "added_edges": added_edges,
            "removed_edges": removed_edges,
        }


class ImpactPreviewService:
    """Build a preview of a pending action's impact on the design graph."""

    @staticmethod
    async def _latest_snapshot_for_session(
        session: AsyncSession, session_id: str
    ) -> Optional[DesignSnapshot]:
        if DesignSnapshot is None:  # snapshot system not present
            return None
        stmt = (
            select(DesignSnapshot)
            .where(DesignSnapshot.session_id == session_id)
            .order_by(DesignSnapshot.created_at.desc())
            .limit(1)
        )
        return await session.scalar(stmt)

    @staticmethod
    def _empty_graph() -> Graph:
        return {"nodes": [], "edges": []}

    @staticmethod
    def _normalize_graph(snap: DesignSnapshot) -> Graph:
        g = getattr(snap, "graph", None) or getattr(snap, "payload", {}) or {}
        nodes = g.get("nodes") or g.get("components") or []
        edges = g.get("edges") or g.get("links") or []
        return {"nodes": deepcopy(nodes), "edges": deepcopy(edges)}

    @staticmethod
    def _ensure_id(obj: Dict[str, Any], prefix: str = "temp") -> str:
        nid = obj.get("id")
        if nid:
            return str(nid)
        import uuid

        nid = f"{prefix}-{uuid.uuid4().hex[:8]}"
        obj["id"] = nid
        return nid

    @staticmethod
    def _apply_action_heuristic(
        graph: Graph, action_type: str, payload: Dict[str, Any]
    ) -> Tuple[Graph, str]:
        g = {"nodes": deepcopy(graph.get("nodes") or []), "edges": deepcopy(graph.get("edges") or [])}
        t = (action_type or "").lower()
        note = ""

        def find_node_idx(nid: str) -> int:
            for i, n in enumerate(g["nodes"]):
                if str(n.get("id")) == str(nid):
                    return i
            return -1

        if any(k in t for k in ["add_component", "component.create", "add_node"]):
            comp = payload.get("component") or payload.get("node") or {
                "type": payload.get("type") or "component",
                "name": payload.get("name"),
            }
            ImpactPreviewService._ensure_id(comp, "node")
            g["nodes"].append(comp)
            note = "Simulated: add node"
        elif any(
            k in t for k in ["remove_component", "component.delete", "remove_node"]
        ):
            nid = payload.get("id") or (payload.get("component") or {}).get("id")
            if nid:
                idx = find_node_idx(nid)
                if idx >= 0:
                    del g["nodes"][idx]
                    note = "Simulated: remove node"
                else:
                    note = "Node id not found; no-op"
            else:
                note = "No node id; no-op"
        elif "update_component" in t or "component.update" in t or "update_node" in t:
            nid = payload.get("id") or (payload.get("component") or {}).get("id")
            fields = payload.get("fields") or (payload.get("component") or {})
            if nid:
                idx = find_node_idx(nid)
                if idx >= 0 and isinstance(fields, dict):
                    g["nodes"][idx] = {
                        **g["nodes"][idx],
                        **fields,
                        "id": g["nodes"][idx].get("id"),
                    }
                    note = "Simulated: update node attributes"
                else:
                    note = "Node not found; no-op"
            else:
                note = "No node id; no-op"
        elif any(k in t for k in ["add_link", "link.create", "add_edge"]):
            link = payload.get("link") or payload
            src = link.get("source") or link.get("from")
            dst = link.get("target") or link.get("to")
            kind = link.get("type") or link.get("kind") or "link"
            if src and dst:
                g["edges"].append({"source": str(src), "target": str(dst), "type": kind})
                note = "Simulated: add edge"
            else:
                note = "Missing link endpoints; no-op"
        elif any(k in t for k in ["remove_link", "link.delete", "remove_edge"]):
            link = payload.get("link") or payload
            src = str(link.get("source") or link.get("from"))
            dst = str(link.get("target") or link.get("to"))
            kind = str(link.get("type") or link.get("kind") or "")
            before_len = len(g["edges"])
            g["edges"] = [
                e
                for e in g["edges"]
                if not (
                    str(e.get("source")) == src
                    and str(e.get("target")) == dst
                    and str(e.get("type") or e.get("kind") or "") == kind
                )
            ]
            if len(g["edges"]) < before_len:
                note = "Simulated: remove edge"
            else:
                note = "Edge not found; no-op"
        else:
            note = (
                "Preview heuristic does not support this action type; showing unchanged graph"
            )

        return g, note

    @staticmethod
    async def build_preview(
        session: AsyncSession, *, pending_id: int, tenant_id: str
    ) -> Dict[str, Any]:
        pa = await session.scalar(
            select(PendingAction).where(
                PendingAction.id == pending_id, PendingAction.tenant_id == tenant_id
            )
        )
        if not pa:
            raise ValueError("Pending action not found")
        if not pa.session_id:
            before_graph = ImpactPreviewService._empty_graph()
            after_graph, note = ImpactPreviewService._apply_action_heuristic(
                before_graph, pa.action_type, pa.payload or {}
            )
            return {
                "before_snapshot": None,
                "after_preview": {
                    "graph": after_graph,
                    "note": f"{note} (no session; baseline empty)",
                },
                "diff": SnapshotDiffService.compute(before_graph, after_graph),
            }

        snap = await ImpactPreviewService._latest_snapshot_for_session(
            session, pa.session_id
        )
        if snap:
            before_graph = ImpactPreviewService._normalize_graph(snap)
            before_meta = {
                "id": getattr(snap, "id", None),
                "created_at": getattr(snap, "created_at", None).isoformat()
                if getattr(snap, "created_at", None)
                else None,
            }
        else:
            before_graph = ImpactPreviewService._empty_graph()
            before_meta = None

        after_graph, note = ImpactPreviewService._apply_action_heuristic(
            before_graph, pa.action_type, pa.payload or {}
        )
        diff = SnapshotDiffService.compute(before_graph, after_graph)
        return {
            "before_snapshot": {"meta": before_meta, "graph": before_graph}
            if before_meta
            else None,
            "after_preview": {"graph": after_graph, "note": note},
            "diff": diff,
        }

