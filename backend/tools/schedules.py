"""
Generate schedules (Cable, Raceway, Termination) from bundle edges produced by expand_connections_v2 (or v1).
Writes schedules to graph.meta.physical.{cables,raceways,terminations} and emits a summary annotation.
Now consumes meta.physical.routes when available to compute real lengths.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, ODLEdge, make_patch


class GenerateSchedulesInput(ToolBase):
    """Pass the edges of the current view so we can scan for kind=='bundle'."""

    view_edges: List[ODLEdge] = Field(default_factory=list)
    routes: List[Dict] = Field(default_factory=list)  # optional: meta.physical.routes


def _collect_bundles(edges: List[ODLEdge] | List[Dict]) -> List[Dict]:
    bundles: List[Dict] = []
    for e in edges:
        try:
            if hasattr(e, "value"):
                src = e.value.get("source_id")
                tgt = e.value.get("target_id")
                kind = e.value.get("kind")
                attrs = e.value.get("attrs", {})
                eid = e.value.get("id")
            elif isinstance(e, dict):
                src = e.get("source_id")
                tgt = e.get("target_id")
                kind = e.get("kind")
                attrs = e.get("attrs", {})
                eid = e.get("id")
            else:
                src = getattr(e, "source_id", None)
                tgt = getattr(e, "target_id", None)
                kind = getattr(e, "kind", None)
                attrs = getattr(e, "attrs", {})
                eid = getattr(e, "id", None)
            if kind == "bundle":
                bundles.append(
                    {
                        "id": eid,
                        "from": src,
                        "to": tgt,
                        "connection": attrs.get("connection"),
                        "conductors": attrs.get("conductors", []),
                        "accessories": attrs.get("accessories", []),
                        "attrs": attrs,
                    }
                )
        except Exception:
            continue
    return bundles


def _length_for_bundle(bid: str, routes: List[Dict], fallback: float = 1.0) -> float:
    for r in routes:
        if r.get("bundle_id") == bid:
            return round(
                sum(seg.get("len_m", 0.0) for seg in r.get("segments", [])), 3
            )
    return fallback


def generate_schedules(inp: GenerateSchedulesInput):
    bundles = _collect_bundles(inp.view_edges)
    cables: List[Dict] = []
    raceways: List[Dict] = []
    terminations: List[Dict] = []
    for b in bundles:
        length_m = _length_for_bundle(
            b["id"], inp.routes, fallback=b.get("attrs", {}).get("length_m", 1.0)
        )
        cables.append(
            {
                "bundle_id": b["id"],
                "from": b["from"],
                "to": b["to"],
                "system": b["connection"],
                "cores": [
                    {"function": c.get("function"), "size": c.get("size")}
                    for c in b["conductors"]
                ],
                "length_m": length_m,
            }
        )
        terminations.append(
            {
                "bundle_id": b["id"],
                "ends": [{"device": b["from"]}, {"device": b["to"]}],
                "lugs": len(
                    [
                        c
                        for c in b["conductors"]
                        if c.get("function") not in ("shield", "DRAIN")
                    ]
                ),
                "glands": len(
                    [a for a in b["accessories"] if a.get("type") == "glands"]
                )
                or 2,
            }
        )
        raceways.append(
            {
                "bundle_id": b["id"],
                "type": "conduit-or-tray",
                "size": "TBD",
                "fill_pct": 0.0,
                "length_m": length_m,
            }
        )

    schedules = {"cables": cables, "raceways": raceways, "terminations": terminations}

    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:schedules",
            op="set_meta",
            value={"path": "physical.schedules", "merge": True, "data": schedules},
        )
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:schedules",
            op="add_edge",
            value={
                "id": f"ann:schedules:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "generate_schedules",
                    "summary": f"{len(cables)} cable(s), {len(terminations)} terminations",
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["generate_schedules", "GenerateSchedulesInput"]

