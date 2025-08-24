"""Compliance checks against electrical standards."""
from __future__ import annotations

from backend.odl.schemas import PatchOp
from .schemas import CheckComplianceInput, make_patch
from .electrical import _worst_case_voc


def check_compliance(inp: CheckComplianceInput):
    findings = []
    if inp.module and inp.dc_series_count and inp.inverter:
        voc_worst = _worst_case_voc(inp.module, inp.env) * inp.dc_series_count
        if voc_worst > inp.inverter.max_system_vdc:
            findings.append(
                {
                    "code": "DC_MAX_V",
                    "severity": "error",
                    "message": f"String Voc {voc_worst:.1f} V exceeds limit {inp.inverter.max_system_vdc} V",
                }
            )
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:compliance",
            op="add_edge",
            value={
                "id": f"ann:compliance:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "check_compliance", "result": {"findings": findings}},
            },
        )
    ]
    return make_patch(inp.request_id, ops)

