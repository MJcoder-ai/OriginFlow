"""
Placeholder generation tool.

Create a number of generic components to enable early design. They are labeled
with attrs['placeholder']=True for downstream replacement.
"""
from __future__ import annotations

from typing import List
from backend.odl.schemas import PatchOp
from backend.tools.schemas import MakePlaceholdersInput, make_patch


def make_placeholders(inp: MakePlaceholdersInput):
    # Very small grid layout so the canvas is readable without
    # "Auto Layout". Each batch starts at (x0,y0); lay out left-to-right
    # then wrap to new rows.
    x0, y0 = (120, 120)
    dx, dy = (180, 140)
    per_row = 8

    ops: List[PatchOp] = []
    for i in range(1, inp.count + 1):
        col = (i - 1) % per_row
        row = (i - 1) // per_row
        x = x0 + col * dx
        y = y0 + row * dy
        nid = f"{inp.placeholder_type}:{inp.request_id}:{i}"
        op_id = f"{inp.request_id}:node:{nid}"
        attrs = dict(inp.attrs)
        attrs.setdefault("placeholder", True)
        attrs.setdefault("x", x)
        attrs.setdefault("y", y)
        ops.append(
            PatchOp(
                op_id=op_id,
                op="add_node",
                value={
                    "id": nid,
                    "type": inp.placeholder_type,
                    "attrs": attrs,
                },
            )
        )
    return make_patch(inp.request_id, ops=ops)
