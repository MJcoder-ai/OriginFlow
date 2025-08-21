"""
Replacement tool – construct an ODLPatch that swaps placeholders for real parts.

This tool is **pure**: it takes replacements and returns an `ODLPatch` with
`update_node` operations that:
  - set `component_master_id` (usually to the part_number)
  - optionally set a new node `type` (e.g., 'generic_panel' → 'panel')
  - clear `attrs.placeholder` and merge any additional attrs
"""
from __future__ import annotations

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


class ReplacementItem(BaseModel):
    node_id: str
    part_number: str
    new_type: Optional[str] = Field(None, description="Override node type if provided")
    attrs: Dict[str, object] = Field(default_factory=dict)


class ReplaceInput(ToolBase):
    replacements: List[ReplacementItem]


def apply_replacements(inp: ReplaceInput):
    ops: List[PatchOp] = []
    for i, repl in enumerate(inp.replacements, start=1):
        update_id = f"{inp.request_id}:upd:{repl.node_id}"
        # Merge attrs and ensure placeholder cleared
        attrs = dict(repl.attrs)
        attrs["placeholder"] = False
        ops.append(
            PatchOp(
                op_id=update_id,
                op="update_node",
                value={
                    "id": repl.node_id,
                    "component_master_id": repl.part_number,
                    **({"type": repl.new_type} if repl.new_type else {}),
                    "attrs": attrs,
                },
            )
        )
    return make_patch(inp.request_id, ops=ops)
