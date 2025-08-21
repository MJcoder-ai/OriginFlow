"""
Structural mounts tool.

For each panel in the current view, add a structural `mount` node and link
them mechanically. New nodes are placed on the 'structural' layer by default.
"""
from __future__ import annotations


from backend.odl.schemas import PatchOp
from backend.tools.schemas import GenerateMountsInput, make_patch


def generate_mounts(inp: GenerateMountsInput):
    panels = [n for n in inp.view_nodes if n.type in {"panel", "generic_panel"}]
    ops: List[PatchOp] = []
    for i, pn in enumerate(panels, start=1):
        mount_id = f"mount:{pn.id}"
        add_node_id = f"{inp.request_id}:node:{mount_id}"
        ops.append(
            PatchOp(
                op_id=add_node_id,
                op="add_node",
                value={
                    "id": mount_id,
                    "type": inp.mount_type,
                    "attrs": {"layer": inp.layer, "auto": True, "for": pn.id},
                },
            )
        )
        edge_id = f"mech:{mount_id}->{pn.id}"
        add_edge_id = f"{inp.request_id}:edge:{edge_id}"
        ops.append(
            PatchOp(
                op_id=add_edge_id,
                op="add_edge",
                value={
                    "id": edge_id,
                    "source_id": mount_id,
                    "target_id": pn.id,
                    "kind": "mechanical",
                    "attrs": {"auto": True},
                },
            )
        )
    return make_patch(inp.request_id, ops=ops)
