"""Analytical helpers for electrical design."""
from __future__ import annotations

from backend.odl.schemas import PatchOp
from .schemas import (
    ApplyBreakerCurveInput,
    CalcVdropInput,
    CalcIfaultInput,
    make_patch,
)
from ._mathutils import loglog_interp


def apply_breaker_curve(inp: ApplyBreakerCurveInput):
    t = loglog_interp(inp.breaker_curve.points, inp.current_multiple)
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


def calculate_voltage_drop(inp: CalcVdropInput):
    if inp.phase == "dc":
        vd = inp.current_A * inp.R_ohm_per_km * (2 * inp.length_m / 1000)
    elif inp.phase == "1ph":
        vd = 2 * inp.current_A * inp.R_ohm_per_km * (inp.length_m / 1000)
    else:
        from math import sqrt

        vd = sqrt(3) * inp.current_A * inp.R_ohm_per_km * (inp.length_m / 1000)
    # Guard against divide-by-zero if misconfigured input slips through
    den = inp.system_v if inp.system_v else 1e-9
    pct = vd / den * 100.0
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

