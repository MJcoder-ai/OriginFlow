from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, ODLEdge, make_patch


class GenerateBOMInput(ToolBase):
    bundles: List[ODLEdge] = Field(default_factory=list)
    schedules: Dict = Field(default_factory=dict)
    equip: Dict = Field(default_factory=dict)


def generate_bom(inp: GenerateBOMInput):
    items = []
    # Equip
    if "module" in inp.equip:
        items.append({
            "sku": inp.equip["module"]["id"],
            "title": inp.equip["module"]["title"],
            "qty": inp.equip.get("array_modules", 0) or 0,
        })
    if "inverter" in inp.equip:
        items.append({
            "sku": inp.equip["inverter"]["id"],
            "title": inp.equip["inverter"]["title"],
            "qty": 1,
        })
    # Cables from schedules
    for row in inp.schedules.get("cables", []):
        items.append({
            "sku": "CABLE",
            "title": f"{row['system']} cable bundle",
            "qty": 1,
            "length_m": row.get("length_m", 0.0),
        })
    # Raceways
    for row in inp.schedules.get("raceways", []):
        items.append({
            "sku": "RACEWAY",
            "title": row["type"],
            "qty": 1,
            "length_m": row.get("length_m", 0.0),
        })
    # Terminations
    for row in inp.schedules.get("terminations", []):
        items.append({
            "sku": "LUGS/GLANDS",
            "title": "Terminations",
            "qty": row.get("lugs", 0) + row.get("glands", 0),
        })
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:bom",
            op="set_meta",
            value={"path": "physical.bom", "merge": True, "data": items},
        )
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:bom",
            op="add_edge",
            value={
                "id": f"ann:bom:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "generate_bom", "summary": f"{len(items)} BOM lines"},
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["GenerateBOMInput", "generate_bom"]

