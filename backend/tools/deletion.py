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
    delete_all = not targets or "*" in targets
    ops: List[PatchOp] = []
    for node in inp.view_nodes:
        ntype = (node.type or "").lower()
        if delete_all or ntype in targets:
            op_id = f"{inp.request_id}:rm:{node.id}"
            ops.append(PatchOp(op_id=op_id, op="remove_node", value={"id": node.id}))

    print(
        f"[delete_nodes] removed={len(ops)} delete_all={delete_all} targets={sorted(targets)}"
    )
    return make_patch(inp.request_id, ops)
