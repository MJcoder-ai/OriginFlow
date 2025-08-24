from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


class MaterializeDesignInput(ToolBase):
    inverter_id: str
    inverter_title: str
    mppts: int
    modules: int
    modules_per_string: int
    strings_parallel: int
    create_edges: bool = True


def _node(node_id: str, type_: str, label: str):
    return {
        "id": node_id,
        "type": type_,
        "label": label,
        "ports": [{"id": "p1"}],
        "attrs": {},
    }


def materialize_design(inp: MaterializeDesignInput):
    ops: List[PatchOp] = []
    if inp.simulate:
        # Only annotate; no node/edge creation
        ops.append(
            PatchOp(
                op_id=f"{inp.request_id}:ann:materialize.sim",
                op="add_edge",
                value={
                    "id": f"ann:mat:{inp.request_id}",
                    "source_id": "__decision__",
                    "target_id": "__design__",
                    "kind": "annotation",
                    "attrs": {
                        "tool": "materialize_design",
                        "summary": f"(simulate) INV + {inp.modules} modules",
                    },
                },
            )
        )
        return make_patch(inp.request_id, ops)

    inv_node_id = "INV1"
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:add:inv",
            op="add_node",
            value=_node(inv_node_id, "string_inverter", inp.inverter_title),
        )
    )
    # Module placeholders
    for i in range(inp.modules):
        nid = f"MOD{i+1}"
        ops.append(
            PatchOp(
                op_id=f"{inp.request_id}:add:mod:{i+1}",
                op="add_node",
                value=_node(nid, "pv_module", f"Module {i+1}"),
            )
        )
    # Simple SLD edges: connect series strings to inverter MPPT A/B...
    if inp.create_edges:
        # connect every module to inverter logically; downstream tools will expand
        for i in range(inp.modules):
            ops.append(
                PatchOp(
                    op_id=f"{inp.request_id}:edge:mod:{i+1}",
                    op="add_edge",
                    value={
                        "id": f"MOD{i+1}->INV1",
                        "source_id": f"MOD{i+1}",
                        "target_id": inv_node_id,
                        "kind": "logical",
                        "attrs": {"note": "string placeholder"},
                    },
                )
            )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:materialize",
            op="add_edge",
            value={
                "id": f"ann:materialize:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "materialize_design",
                    "summary": f"Created 1 inverter + {inp.modules} modules",
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["MaterializeDesignInput", "materialize_design"]

