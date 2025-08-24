"""
Generate schedules (Cable, Raceway, Termination) from bundle edges produced by expand_connections_v2 (or v1).
Writes schedules to graph.meta.physical.{cables,raceways,terminations} and emits a summary annotation.
"""
from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, ODLEdge, make_patch


class GenerateSchedulesInput(ToolBase):
    """Pass the edges of the current view so we can scan for kind=='bundle'."""

    view_edges: List[ODLEdge] = Field(default_factory=list)


def _collect_bundles(edges: List[ODLEdge]) -> List[Dict]:
    bundles: List[Dict] = []
    for e in edges:
        try:
            kind = e.value.get("kind") if hasattr(e, "value") else e.get("kind")
            attrs = e.value.get("attrs") if hasattr(e, "value") else e.get("attrs", {})
            if kind == "bundle":
                bundles.append(
                    {
                        "id": e.value.get("id") if hasattr(e, "value") else e.get("id"),
                        "from": e.value.get("source_id") if hasattr(e, "value") else e.get("source_id"),
                        "to": e.value.get("target_id") if hasattr(e, "value") else e.get("target_id"),
                        "connection": attrs.get("connection"),
                        "conductors": attrs.get("conductors", []),
                        "accessories": attrs.get("accessories", []),
                    }
                )
        except Exception:
            continue
    return bundles


def generate_schedules(inp: GenerateSchedulesInput):
    bundles = _collect_bundles(inp.view_edges)
    cables: List[Dict] = []
    raceways: List[Dict] = []
    terminations: List[Dict] = []
    for b in bundles:
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
                "length_m": 1.0,
            }
        )
        terminations.append(
            {
                "bundle_id": b["id"],
                "ends": [{"device": b["from"]}, {"device": b["to"]}],
                "lugs": len([
                    c
                    for c in b["conductors"]
                    if c.get("function") not in ("shield", "DRAIN")
                ]),
                "glands": len([a for a in b["accessories"] if a.get("type") == "glands"]) or 2,
            }
        )
        raceways.append(
            {
                "bundle_id": b["id"],
                "type": "conduit-or-tray",
                "size": "TBD",
                "fill_pct": 0.0,
                "length_m": 1.0,
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

