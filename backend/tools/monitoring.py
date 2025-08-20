"""
Monitoring device tool.

Add a single 'monitoring' node and connect all inverters in view to it with
'data' edges. Useful for basic connectivity validation.
"""
from __future__ import annotations

from typing import List
from backend.odl.schemas import PatchOp
from backend.tools.schemas import AddMonitoringInput, make_patch


def add_monitoring_device(inp: AddMonitoringInput):
    inverters = [n for n in inp.view_nodes if n.type in {"inverter", "generic_inverter"}]
    if not inverters:
        return make_patch(inp.request_id, ops=[])

    mon_id = f"mon:{inp.session_id}"
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:node:{mon_id}",
            op="add_node",
            value={
                "id": mon_id,
                "type": inp.device_type,
                "attrs": {"layer": inp.layer, "auto": True},
            },
        )
    )
    for inv in inverters:
        edge_id = f"data:{inv.id}->{mon_id}"
        ops.append(
            PatchOp(
                op_id=f"{inp.request_id}:edge:{edge_id}",
                op="add_edge",
                value={
                    "id": edge_id,
                    "source_id": inv.id,
                    "target_id": mon_id,
                    "kind": "data",
                    "attrs": {"auto": True},
                },
            )
        )
    return make_patch(inp.request_id, ops=ops)
