"""
Compliance v2: DC max voltage, MPPT window fit, ampacity vs OCPD, voltage drop.
Consumes explicit inputs (module/inverter selections, conductor choices) or falls back to meta.design_state hints.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from backend.odl.schemas import PatchOp
from backend.tools.schemas import ToolBase, make_patch
from backend.tools.standards_profiles import load_profile, default_vdrop_pct


class Env(BaseModel):
    site_tmin_C: float
    site_tmax_C: float
    code_profile: str = "NEC_2023"


class Module(BaseModel):
    voc_stc: float
    vmp: float
    isc_stc: float
    beta_voc_pct_per_C: float


class MPPT(BaseModel):
    v_min: float
    v_max: float
    count: int = 1


class Inverter(BaseModel):
    max_system_vdc: float
    mppt: MPPT
    ac_inom_A: float | None = None


class ConductorChoice(BaseModel):
    size: str
    ampacity_A: float
    vdrop_pct: float


class OCPD(BaseModel):
    rating_A: int


class CheckComplianceV2Input(ToolBase):
    env: Env
    module: Optional[Module] = None
    inverter: Optional[Inverter] = None
    dc_series_count: Optional[int] = None
    dc_parallel_strings: Optional[int] = None
    dc_ocpd: Optional[OCPD] = None
    ac_conductor: Optional[ConductorChoice] = None
    circuit_kind: Optional[str] = None  # "dc_string" | "ac_feeder" etc.


def _voc_at_t(module: Module, tC: float, ref: float = 25.0) -> float:
    dv = module.beta_voc_pct_per_C * (tC - ref)
    return module.voc_stc * (1.0 + dv / 100.0)


def check_compliance_v2(inp: CheckComplianceV2Input):
    prof = load_profile(inp.env.code_profile)
    findings: List[Dict] = []

    if inp.module and inp.dc_series_count and inp.inverter:
        voc_worst_string = _voc_at_t(inp.module, inp.env.site_tmin_C) * inp.dc_series_count
        if voc_worst_string > inp.inverter.max_system_vdc:
            findings.append(
                {
                    "code": "DC_MAX_V",
                    "severity": "error",
                    "message": f"Worst-case Voc {voc_worst_string:.1f} V exceeds system limit {inp.inverter.max_system_vdc:.0f} V",
                    "suggest": "Reduce modules per string or choose equipment rated for higher system voltage",
                }
            )
        vmp_string = inp.module.vmp * inp.dc_series_count
        if not (inp.inverter.mppt.v_min <= vmp_string <= inp.inverter.mppt.v_max):
            findings.append(
                {
                    "code": "MPPT_WINDOW",
                    "severity": "warn",
                    "message": f"String Vmp {vmp_string:.1f} V outside MPPT window [{inp.inverter.mppt.v_min}, {inp.inverter.mppt.v_max}] V",
                    "suggest": "Adjust series count to fall within MPPT window",
                }
            )

    if inp.ac_conductor and inp.dc_ocpd:
        if inp.ac_conductor.ampacity_A < inp.dc_ocpd.rating_A:
            findings.append(
                {
                    "code": "AMPACITY_LT_OCPD",
                    "severity": "error",
                    "message": f"Conductor ampacity {inp.ac_conductor.ampacity_A:.1f}A < OCPD {inp.dc_ocpd.rating_A}A",
                    "suggest": "Upsize conductor or select smaller OCPD if permitted",
                }
            )

    if inp.ac_conductor and inp.circuit_kind:
        target = default_vdrop_pct(inp.circuit_kind, prof)
        if inp.ac_conductor.vdrop_pct > target:
            findings.append(
                {
                    "code": "VOLTAGE_DROP",
                    "severity": "warn",
                    "message": f"Voltage drop {inp.ac_conductor.vdrop_pct:.2f}% exceeds target {target:.2f}%",
                    "suggest": "Increase conductor size or shorten route",
                }
            )

    ops = []
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:compliance_v2",
            op="add_edge",
            value={
                "id": f"ann:compliance_v2:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {"tool": "check_compliance_v2", "result": {"findings": findings}},
            },
        )
    )
    return make_patch(inp.request_id, ops)


__all__ = [
    "check_compliance_v2",
    "CheckComplianceV2Input",
    "Env",
    "Module",
    "Inverter",
    "MPPT",
    "ConductorChoice",
    "OCPD",
]

