"""Communication planning tools."""
from __future__ import annotations

from backend.odl.schemas import PatchOp
from .schemas import LinkBudgetPlannerInput, make_patch


def link_budget_planner(inp: LinkBudgetPlannerInput):
    ok = True
    notes = "RS-485 typical max segment length ~1200 m"
    if inp.topology == "rs485_multi_drop" and inp.segment_length_m > 1200:
        ok = False
        notes = "Segment exceeds RS-485 guidance"
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:link",
            op="add_edge",
            value={
                "id": f"ann:link:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "link_budget_planner", "ok": ok, "notes": notes},
            },
        )
    ]
    return make_patch(inp.request_id, ops)

