"""
Wiring generation tool.

Given a view of nodes, generate simple electrical edges between panels and the
nearest (first) inverter. This is deliberately simple and deterministic so we
can validate the ODL patch flow end-to-end.
"""
from __future__ import annotations


from backend.odl.schemas import PatchOp
from backend.tools.schemas import GenerateWiringInput, make_patch


def generate_wiring(inp: GenerateWiringInput):
    # Pick the first inverter (if any)
    inverters = [n for n in inp.view_nodes if n.type in {"inverter", "generic_inverter"}]
    if not inverters:
        # Nothing to connect to, return empty patch
        return make_patch(inp.request_id, ops=[])
    inv = inverters[0]

    panel_nodes = [n for n in inp.view_nodes if n.type in {"panel", "generic_panel"}]
    ops: List[PatchOp] = []
    for i, pn in enumerate(panel_nodes, start=1):
        edge_id = f"wire:{pn.id}->{inv.id}"
        op_id = f"{inp.request_id}:edge:{edge_id}"
        ops.append(
            PatchOp(
                op_id=op_id,
                op="add_edge",
                value={
                    "id": edge_id,
                    "source_id": pn.id,
                    "target_id": inv.id,
                    "kind": inp.edge_kind,
                    "attrs": {"auto": True},
                },
            )
        )
    return make_patch(inp.request_id, ops=ops)
