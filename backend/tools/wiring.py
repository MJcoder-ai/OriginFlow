"""
Wiring generation tool.

Given a view of nodes, connect the first inverter to all panel nodes. This
skips generic placeholders so wiring only appears once real component types
exist. The patch is deterministic for idempotency tests.
"""
from __future__ import annotations

from typing import List

from backend.odl.schemas import PatchOp
from backend.tools.schemas import GenerateWiringInput, make_patch


def generate_wiring(inp: GenerateWiringInput):
    # Pick the first typed inverter (if any)
    inverters = [n for n in inp.view_nodes if n.type == "inverter"]
    panels = [n for n in inp.view_nodes if n.type == "panel"]
    if not inverters or not panels:
        # Nothing to connect to – return empty patch
        # (applying still bumps version)
        return make_patch(inp.request_id, ops=[])
    inv = inverters[0]

    ops: List[PatchOp] = []
    for i, pn in enumerate(panels, start=1):
        edge_id = f"wire:{inv.id}:{pn.id}"
        op_id = f"{inp.request_id}:e:{i}"
        ops.append(
            PatchOp(
                op_id=op_id,
                op="add_edge",
                value={
                    "id": edge_id,
                    "source_id": inv.id,
                    "target_id": pn.id,
                    "kind": inp.edge_kind,
                    "attrs": {"auto": True},
                },
            )
        )
    return make_patch(inp.request_id, ops=ops)
