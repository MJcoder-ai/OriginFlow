"""
Compute & persist Design State for the active view.
Writes to graph.meta.design_state via a set_meta PatchOp and emits an annotation for audit.
"""
from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, ODLNode, make_patch
from backend.tools.standards_profiles import (
    StandardsProfile,
    load_profile,
    temp_correction_factor,
    grouping_factor,
    default_vdrop_pct,
)


class Env(BaseModel):
    site_tmin_C: float
    site_tmax_C: float
    code_profile: str = "NEC_2023"
    elevation_m: float | None = None
    utility_voltage: str | None = None  # e.g. "480V_3P"


class Module(BaseModel):
    id: str
    voc_stc: float
    vmp: float
    isc_stc: float
    imp: float
    beta_voc_pct_per_C: float


class InverterWindow(BaseModel):
    v_min: float
    v_max: float
    count: int = 1


class Inverter(BaseModel):
    id: str
    max_system_vdc: float
    windows: List[InverterWindow]
    ac_inom_A: float | None = None
    ac_phase: str | None = None
    ac_v_ll: float | None = None


class ComputeDesignStateInput(ToolBase):
    view_nodes: List[ODLNode] = Field(default_factory=list)
    env: Env
    modules: List[Module] = Field(default_factory=list)
    inverters: List[Inverter] = Field(default_factory=list)


def _worst_case_voc_stc(module: Module, tmin: float, ref: float = 25.0) -> float:
    dv = module.beta_voc_pct_per_C * (tmin - ref)
    return module.voc_stc * (1.0 + dv / 100.0)


def compute_design_state(inp: ComputeDesignStateInput):
    prof: StandardsProfile = load_profile(inp.env.code_profile)
    counts = {
        "modules": len(inp.modules),
        "inverters": len(inp.inverters),
        "nodes": len(inp.view_nodes),
    }

    strings: List[Dict] = []
    for inv in inp.inverters:
        for m in inp.modules:
            voc_worst = _worst_case_voc_stc(m, inp.env.site_tmin_C)
            for win in inv.windows:
                max_series_voltage = inv.max_system_vdc
                max_series = int((max_series_voltage // max(voc_worst, 1e-6)))
                strings.append(
                    {
                        "module_id": m.id,
                        "inverter_id": inv.id,
                        "mppt_v_min": win.v_min,
                        "mppt_v_max": win.v_max,
                        "mppt_count": win.count,
                        "voc_worst_module": voc_worst,
                        "max_series_by_system": max_series,
                    }
                )

    derate_display = {
        "temp_factor_90C": temp_correction_factor(inp.env.site_tmax_C, prof),
        "grouping_factor_3ccc": grouping_factor(3, prof),
        "default_vdrop_pct": {
            "dc_string": default_vdrop_pct("dc_string", prof),
            "ac_branch": default_vdrop_pct("ac_branch", prof),
            "ac_feeder": default_vdrop_pct("ac_feeder", prof),
            "ctl": default_vdrop_pct("ctl", prof),
            "comm": default_vdrop_pct("comm", prof),
        },
    }

    state = {
        "env": inp.env.model_dump(),
        "counts": counts,
        "strings": strings,
        "derate_defaults": derate_display,
    }

    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:design_state",
            op="set_meta",
            value={"path": "design_state", "merge": True, "data": state},
        )
    )
    summary = (
        f"DesignState: {counts['modules']} modules, {counts['inverters']} inverters; "
        f"Tmin={inp.env.site_tmin_C}°C, Tmax={inp.env.site_tmax_C}°C."
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:design_state",
            op="add_edge",
            value={
                "id": f"ann:design_state:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "compute_design_state",
                    "summary": summary,
                    "state_ref": "meta.design_state",
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = ["compute_design_state", "ComputeDesignStateInput", "Env", "Module", "Inverter", "InverterWindow"]

