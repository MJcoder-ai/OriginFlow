from __future__ import annotations
from typing import Dict, List
from pydantic import BaseModel
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


class Module(BaseModel):
    isc: float


class SelectOcpDcInput(ToolBase):
    strings_parallel: int
    module: Module


def select_ocp_dc(inp: SelectOcpDcInput):
    findings = []
    result: Dict = {"string_fusing_required": False, "fuse_A": None}
    if inp.strings_parallel >= 3:
        result["string_fusing_required"] = True
        # Rule-of-thumb: ≥ 1.25× Isc at expected temperature; keep simple here
        fuse = int(round(max(15, 1.25 * inp.module.isc)))
        # round up to standard size
        std = [10, 15, 20, 25, 30]
        result["fuse_A"] = min([s for s in std if s >= fuse] or [30])
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:ocpdc",
            op="add_edge",
            value={
                "id": f"ann:ocpdc:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "select_ocp_dc", "result": result, "findings": findings},
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["Module", "SelectOcpDcInput", "select_ocp_dc"]

