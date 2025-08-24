"""Electrical design tools.

Pure functions for PV stringing, protective device selection, conductor sizing
and connection expansion.  Each tool accepts typed input and returns an
ODLPatch with annotation edges describing the decision for auditability.
"""
from __future__ import annotations

from math import log10
from typing import List

from backend.odl.schemas import PatchOp
from .schemas import (
    SelectDcStringingInput,
    SelectOcpDcInput,
    SelectOcpAcInput,
    SelectConductorsInput,
    ExpandConnectionsInput,
    BreakerSpec,
    ConductorChoice,
    make_patch,
)


# ---------- helpers ----------

def _worst_case_voc(module, env, ref_C: float = 25.0) -> float:
    dv_pct = module.beta_voc_pct_per_C * (env.ambient_min_C - ref_C)
    return module.voc_stc * (1.0 + dv_pct / 100.0)


def _loglog_interp(points, x: float) -> float:
    pts = sorted(points, key=lambda p: p[0])
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x1 <= x <= x2:
            from math import log10

            lx1, lx2 = log10(x1), log10(x2)
            ly1, ly2 = log10(y1), log10(y2)
            t = (log10(x) - lx1) / (lx2 - lx1)
            ly = ly1 + t * (ly2 - ly1)
            return 10 ** ly
    return pts[-1][1]


def _vdrop_dc(I: float, ohm_km: float, L_m: float) -> float:
    return I * ohm_km * (2 * L_m / 1000)


def _vdrop_ac_1ph(I: float, ohm_km: float, L_m: float) -> float:
    return 2 * I * ohm_km * (L_m / 1000)


def _vdrop_ac_3ph(I: float, ohm_km: float, L_m: float) -> float:
    from math import sqrt

    return sqrt(3) * I * ohm_km * (L_m / 1000)


# ---------- tools ----------

def select_dc_stringing(inp: SelectDcStringingInput):
    """Determine safe PV string size and create a symbolic DC connection."""

    voc_worst = _worst_case_voc(inp.module, inp.env)
    window = inp.inverter.dc_windows[0] if inp.inverter.dc_windows else None
    max_series = int((inp.inverter.max_system_vdc * inp.series_margin_pct) // voc_worst)
    vmp_target = inp.module.vmp
    if window:
        series = max(1, min(max_series, int(window.v_max // vmp_target)))
    else:
        series = max(1, max_series)
    strings = max(1, min(inp.parallel_limit, inp.desired_module_count // series))
    mppt_count = window.mppt_count if window else 1
    strings_per_mppt = [strings // mppt_count] * mppt_count
    for i in range(strings % mppt_count):
        strings_per_mppt[i] += 1

    decision = {
        "series_per_string": series,
        "parallel_strings": strings,
        "strings_per_mppt": strings_per_mppt,
        "voc_worst": voc_worst * series,
        "vmp_string": inp.module.vmp * series,
    }

    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:dc_stringing",
            op="add_edge",
            value={
                "id": f"ann:dc_stringing:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "select_dc_stringing", "decision": decision},
            },
        )
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:edge:dc_bus",
            op="add_edge",
            value={
                "id": f"dc_bus:{inp.request_id}",
                "source_id": "inverter_1",
                "target_id": "pv_array_1",
                "kind": "electrical",
                "attrs": {
                    "dc": True,
                    "series": series,
                    "parallel": strings,
                    "conductors": [
                        {"function": "PV+", "count": 1},
                        {"function": "PV-", "count": 1},
                        {"function": "EGC", "count": 1},
                    ],
                },
            },
        )
    )
    return make_patch(inp.request_id, ops)


def select_ocp_dc(inp: SelectOcpDcInput):
    I_cont = inp.isc_stc_per_string * inp.cont_factor
    size = next((s for s in sorted(inp.fuse_catalog_A) if s >= I_cont), max(inp.fuse_catalog_A))
    fuse_required = inp.n_parallel_strings > inp.require_fusing_if_parallel_gt
    decision = {
        "fuse_required": fuse_required,
        "recommended_A": size,
        "calc_continuous_A": I_cont,
    }
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:ocpdc",
            op="add_edge",
            value={
                "id": f"ann:ocp_dc:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "select_ocp_dc", "decision": decision},
            },
        )
    )
    if fuse_required:
        ops.append(
            PatchOp(
                op_id=f"{inp.request_id}:edge:fuses",
                op="add_edge",
                value={
                    "id": f"fuses:{inp.request_id}",
                    "source_id": "pv_array_1",
                    "target_id": "combiner_1",
                    "kind": "protection",
                    "attrs": {"device": "fuse", "rating_A": size, "qty": inp.n_parallel_strings},
                },
            )
        )
    return make_patch(inp.request_id, ops)


def select_ocp_ac(inp: SelectOcpAcInput):
    I_nom = float(inp.inverter.ac_inom_A or 0.0)
    I_cont = I_nom * inp.cont_factor
    candidates = [b for b in inp.breaker_library if b.rating_A >= I_cont and b.series_sc_rating_ka >= inp.min_sc_rating_ka]
    if candidates:
        b = min(candidates, key=lambda x: x.rating_A)
        ok = True
    else:
        b = max(inp.breaker_library, key=lambda x: x.rating_A)
        ok = b.series_sc_rating_ka >= inp.min_sc_rating_ka
    decision = {
        "breaker_rating_A": b.rating_A,
        "frame_A": b.frame_A,
        "poles": b.poles,
        "curve_points": b.curve.points,
        "satisfies_sc_rating": ok,
        "thermal_cont_ok": b.rating_A >= I_cont,
    }
    ops: List[PatchOp] = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:ocpac",
            op="add_edge",
            value={
                "id": f"ann:ocp_ac:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "select_ocp_ac", "decision": decision},
            },
        )
    )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:edge:breaker",
            op="add_edge",
            value={
                "id": f"ac_breaker:{inp.request_id}",
                "source_id": "inverter_1",
                "target_id": "ac_bus_1",
                "kind": "protection",
                "attrs": {"device": "breaker", "rating_A": b.rating_A, "poles": b.poles},
            },
        )
    )
    return make_patch(inp.request_id, ops)


def select_conductors(inp: SelectConductorsInput):
    I = inp.current_A
    L = inp.env.length_m
    target_v = inp.system_v * inp.env.max_vdrop_pct / 100.0

    def vdrop_for(size_label: str) -> float:
        ohm_km_map = {
            "14AWG": 8.286,
            "12AWG": 5.211,
            "10AWG": 3.277,
            "8AWG": 2.061,
            "6AWG": 1.296,
            "4AWG": 0.815,
            "2AWG": 0.513,
            "1/0": 0.324,
            "2/0": 0.257,
            "3/0": 0.204,
            "4/0": 0.162,
        }
        ohm_km = ohm_km_map[size_label] * (
            inp.resistivity_ohm_km[inp.env.material] / 0.018
        )
        if inp.phase == "dc":
            return _vdrop_dc(I, ohm_km, L)
        if inp.phase == "1ph":
            return _vdrop_ac_1ph(I, ohm_km, L)
        return _vdrop_ac_3ph(I, ohm_km, L)

    candidates: List[ConductorChoice] = []
    for size, base_amp in inp.ampacity_table_A.items():
        amp = base_amp * inp.derate_ambient_pct * inp.derate_bundling_pct
        vd = vdrop_for(size)
        candidates.append(
            ConductorChoice(
                size_awg_or_kcmil=size,
                vdrop_pct=vd / inp.system_v * 100.0,
                ampacity_A=amp,
            )
        )
    acceptable = [c for c in candidates if c.ampacity_A >= I and c.vdrop_pct <= inp.env.max_vdrop_pct]
    choice = acceptable[0] if acceptable else max(candidates, key=lambda c: c.ampacity_A)
    decision = {"choice": choice.model_dump(), "candidates": [c.model_dump() for c in acceptable[:3]]}
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:conductors",
            op="add_edge",
            value={
                "id": f"ann:conductors:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "select_conductors", "decision": decision},
            },
        )
    ]
    return make_patch(inp.request_id, ops)


def expand_connections(inp: ExpandConnectionsInput):
    if inp.connection_type == "dc_pv":
        funcs = ["PV+", "PV-"]
        if inp.add_ground:
            funcs.append("EGC")
    elif inp.connection_type == "ac_3ph_4w":
        funcs = ["L1", "L2", "L3", "N"]
        if inp.add_ground:
            funcs.append("PE")
    elif inp.connection_type == "ac_1ph_2w":
        funcs = ["L", "N"]
        if inp.add_ground:
            funcs.append("PE")
    else:
        funcs = ["A", "B"]
    ops: List[PatchOp] = []
    for idx, f in enumerate(funcs):
        ops.append(
            PatchOp(
                op_id=f"{inp.request_id}:edge:{idx}",
                op="add_edge",
                value={
                    "id": f"{inp.source_id}:{f}->{inp.target_id}:{f}:{inp.connection_type}",
                    "source_id": inp.source_id,
                    "target_id": inp.target_id,
                    "kind": "electrical",
                    "attrs": {"function": f, "count": 1},
                },
            )
        )
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:expand",
            op="add_edge",
            value={
                "id": f"ann:expand:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "expand_connections", "functions": funcs},
            },
        )
    )
    return make_patch(inp.request_id, ops)

