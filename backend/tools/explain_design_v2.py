"""
Create a plain-English explanation of the current design state for non-technical users.
Emits an annotation with 'audience' and bullet points; engineering details remain in meta.design_state.
"""
from __future__ import annotations
from typing import Dict, Any, List
from pydantic import BaseModel
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


class ExplainDesignV2Input(ToolBase):
    design_state: Dict[str, Any]
    audience: str = "non-technical"  # or "engineering"


def _nl_summary(ds: Dict[str, Any], audience: str) -> List[str]:
    env = ds.get("env", {})
    counts = ds.get("counts", {})
    bullets = []
    bullets.append(
        f"This design connects {counts.get('modules', 0)} solar modules to {counts.get('inverters', 0)} inverter(s)."
    )
    bullets.append(
        f"It accounts for local temperatures from {env.get('site_tmin_C')}°C to {env.get('site_tmax_C')}°C to keep voltages safe."
    )
    if audience == "engineering":
        strings = ds.get("strings", [])[:1]
        if strings:
            s = strings[0]
            bullets.append(
                f"Worst-case module Voc at Tmin is {s.get('voc_worst_module'):.2f} V; max series allowed by system is {s.get('max_series_by_system')}.")
        dd = ds.get("derate_defaults", {})
        bullets.append(
            f"Default derates: temp {dd.get('temp_factor_90C')}, grouping {dd.get('grouping_factor_3ccc')}."
        )
    else:
        bullets.append("Wiring, protection, and cable sizes are chosen to avoid overheating and power loss.")
        bullets.append("The system is checked against electrical code rules automatically.")
    return bullets


def explain_design_v2(inp: ExplainDesignV2Input):
    bullets = _nl_summary(inp.design_state, inp.audience)
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:explain_v2",
            op="add_edge",
            value={
                "id": f"ann:explain_v2:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "explain_design_v2",
                    "audience": inp.audience,
                    "bullets": bullets,
                },
            },
        )
    ]
    return make_patch(inp.request_id, ops)


__all__ = ["explain_design_v2", "ExplainDesignV2Input"]

