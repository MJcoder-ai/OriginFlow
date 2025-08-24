from __future__ import annotations
from math import ceil
from typing import Dict, List
from pydantic import BaseModel
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch


class Env(BaseModel):
    site_tmin_C: float


class Module(BaseModel):
    p_W: float
    voc: float
    vmp: float
    imp: float
    beta_voc_pct_per_C: float


class MpptWindow(BaseModel):
    v_min: float
    v_max: float
    count: int = 1


class Inverter(BaseModel):
    max_system_vdc: float
    mppt_windows: List[MpptWindow]


class SelectStringingInput(ToolBase):
    target_kw_stc: float
    env: Env
    module: Module
    inverter: Inverter
    margin_voc_pct: float = 0.02  # headroom vs system Vdc


def _voc_cold(voc_stc: float, beta_pct_perC: float, tmin: float, ref: float = 25.0) -> float:
    dv = beta_pct_perC * (tmin - ref)
    return voc_stc * (1.0 + dv / 100.0)


def select_dc_stringing(inp: SelectStringingInput):
    target_W = inp.target_kw_stc * 1000
    n_modules = max(1, round(target_W / inp.module.p_W))

    voc_cold = _voc_cold(inp.module.voc, inp.module.beta_voc_pct_per_C, inp.env.site_tmin_C)
    sys_lim = inp.inverter.max_system_vdc * (1.0 - inp.margin_voc_pct)
    # Pick max N satisfying Voc_cold*N <= sys_lim and Vmp*N within any MPPT window
    best = None
    for N in range(4, 20):  # practical residential range
        vocN = voc_cold * N
        vmpN = inp.module.vmp * N
        if vocN > sys_lim:
            break
        fits = any(w.v_min <= vmpN <= w.v_max for w in inp.inverter.mppt_windows)
        if not fits:
            continue
        best = N
    if best is None:
        # fallback: smallest N under system voltage
        for N in range(2, 20):
            if voc_cold * N <= sys_lim:
                best = N
                break
    N = best or 6
    S_total = ceil(n_modules / N)
    mppt_total = sum(w.count for w in inp.inverter.mppt_windows)
    # spread strings across MPPTs as evenly as possible
    alloc = [0] * mppt_total
    for i in range(S_total):
        alloc[i % mppt_total] += 1

    strings = {
        "series": N,
        "parallel": S_total,
        "mppt_allocation": alloc,
        "array_modules": int(N * S_total),
        "array_kw_stc": round((N * S_total * inp.module.p_W) / 1000, 3),
        "voc_cold_string_V": round(voc_cold * N, 2),
        "vmp_string_V": round(inp.module.vmp * N, 2),
    }
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:meta:strings",
            op="set_meta",
            value={"path": "design_state.strings", "merge": True, "data": strings},
        )
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:strings",
            op="add_edge",
            value={
                "id": f"ann:strings:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "select_dc_stringing",
                    "summary": f"N={N}, S={S_total}, Voc_cold={strings['voc_cold_string_V']} V",
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = [
    "Env",
    "Module",
    "Inverter",
    "MpptWindow",
    "SelectStringingInput",
    "select_dc_stringing",
]

