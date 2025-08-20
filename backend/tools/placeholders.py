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
    ops: List[PatchOp] = []
    for i in range(inp.count):
        nid = f"{inp.placeholder_type}:{inp.request_id}:{i + 1}"
        op_id = f"{inp.request_id}:node:{nid}"
        attrs = dict(inp.attrs)
        attrs.setdefault("placeholder", True)
        ops.append(
            PatchOp(
                op_id=op_id,
                op="add_node",
                value={"id": nid, "type": inp.placeholder_type, "attrs": attrs},
            )
        )
    return make_patch(inp.request_id, ops=ops)
