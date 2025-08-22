"""Delete nodes tool.

Removes all nodes of specified component types from the current view.
"""
from __future__ import annotations

from typing import List

from backend.odl.schemas import PatchOp
from backend.tools.schemas import DeleteNodesInput, make_patch


def delete_nodes(inp: DeleteNodesInput):
    """Return an ODLPatch that removes nodes matching component types."""
    targets = {t.lower() for t in inp.component_types}
    ops: List[PatchOp] = []
    for node in inp.view_nodes:
        ntype = (node.type or "").lower()
        if ntype in targets:
            op_id = f"{inp.request_id}:rm:{node.id}"
            ops.append(PatchOp(op_id=op_id, op="remove_node", value={"id": node.id}))
    return make_patch(inp.request_id, ops)
