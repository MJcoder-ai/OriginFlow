"""Analytical helpers for electrical design."""
from __future__ import annotations

from backend.odl.schemas import PatchOp
from .schemas import (
    ApplyBreakerCurveInput,
    CalcVdropInput,
    CalcIfaultInput,
    make_patch,
)


def apply_breaker_curve(inp: ApplyBreakerCurveInput):
    t = _loglog_interp(inp.breaker_curve.points, inp.current_multiple)
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:curve",
            op="add_edge",
            value={
                "id": f"ann:curve:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "apply_breaker_curve", "result": {"t_trip_s": t}},
            },
        )
    ]
    return make_patch(inp.request_id, ops)


def _loglog_interp(points, x: float) -> float:
    pts = sorted(points, key=lambda p: p[0])
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    from math import log10

    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x1 <= x <= x2:
            lx1, lx2 = log10(x1), log10(x2)
            ly1, ly2 = log10(y1), log10(y2)
            t = (log10(x) - lx1) / (lx2 - lx1)
            ly = ly1 + t * (ly2 - ly1)
            return 10 ** ly
    return pts[-1][1]


def calculate_voltage_drop(inp: CalcVdropInput):
    if inp.phase == "dc":
        vd = inp.current_A * inp.R_ohm_per_km * (2 * inp.length_m / 1000)
    elif inp.phase == "1ph":
        vd = 2 * inp.current_A * inp.R_ohm_per_km * (inp.length_m / 1000)
    else:
        from math import sqrt

        vd = sqrt(3) * inp.current_A * inp.R_ohm_per_km * (inp.length_m / 1000)
    pct = vd / inp.system_v * 100.0
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:vdrop",
            op="add_edge",
            value={
                "id": f"ann:vdrop:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "calculate_voltage_drop", "result": {"v_drop_V": vd, "v_drop_pct": pct}},
            },
        )
    ]
    return make_patch(inp.request_id, ops)


def calculate_fault_current(inp: CalcIfaultInput):
    results = {}
    if inp.dc_isc_stc and inp.dc_parallel_strings:
        results["dc_fault_A"] = inp.dc_isc_stc * inp.dc_parallel_strings * inp.dc_multiplier
    if inp.ac_inverter_inom:
        results["ac_fault_A"] = inp.ac_inverter_inom * inp.ac_fault_multiple
    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:ann:ifault",
            op="add_edge",
            value={
                "id": f"ann:ifault:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "calculate_fault_current", "result": results},
            },
        )
    ]
    return make_patch(inp.request_id, ops)

