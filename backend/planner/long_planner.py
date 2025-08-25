from __future__ import annotations
import math
import re
from typing import Optional

from .schema import LongPlan, PlanTask, LongPlanCard

KW_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:kw|kW)", re.I)


def _extract_kw(text: str) -> Optional[float]:
    m = KW_RE.search(text or "")
    return float(m.group(1)) if m else None


class LongPlanner:
    """State-aware planner producing a multi-step plan for PV design.

    This simplified version does not inspect existing ODL state but derives
    a sequence of standard tool invocations based on requested system size.
    """

    def __init__(self, store: object | None = None):
        self.store = store

    async def plan(self, session_id: str, text: str, layer: str) -> LongPlanCard:
        kw = _extract_kw(text) or 3.0
        module_w = 400.0
        panel_count = math.ceil(kw * 1000.0 / module_w)
        rationale = (
            f"Target ≈{kw:.1f} kWdc using ≈{module_w:.0f} W modules → {panel_count} panels.\n"
            "Use 1x string inverter, then perform stringing and protection sizing."
        )

        # MLPE mode inference from text (microinverters / optimizers / none)
        mlpe = "none"
        t = (text or "").lower()
        if "micro" in t: mlpe = "microinverter"
        elif "optimizer" in t or "mlpe" in t: mlpe = "optimizer"

        tasks: list[PlanTask] = [
            PlanTask(
                id="pv_set_assumptions",
                title="Set environment, service, and targets",
                args={"env": {"tmin_C": -10.0, "tmax_C": 45.0, "utility": "120/240V"},
                      "targets": {"dc_vdrop_pct": 2.0, "ac_vdrop_pct": 3.0},
                      "service": {"bus_A": 200, "main_A": 200, "interconnection": "load_side"},
                      "profile": "NEC_2023",
                      "layer": layer},
                layer=layer,
                can_auto=True,
                rationale="Safe defaults; edit later in Assumptions panel."
            ),
            PlanTask(
                id="pv_select_components",
                title="Select inverter + module placeholders",
                args={
                    "inverter_hint": {"topology": "string", "ac_kw": max(kw, 3.0), "mppt": 2, "vdc_max": 600,
                                      "mppt_vmin": 200, "mppt_vmax": 550},
                    "module_hint": {"p_mp": module_w, "voc": 49.5, "vmp": 41.5, "isc": 11.2, "imp": 10.7, "temp_coeff_voc_pct_per_c": -0.28},
                    "panel_count": panel_count,
                    "mlpe": mlpe,
                    "layer": layer,
                },
                layer=layer,
                can_auto=True,
                rationale=rationale,
            ),
            # Mechanical layer planning (surface → racking → attachment check)
            PlanTask(
                id="mech_surface",
                title="Define roof surface (single plane)",
                args={"name":"R1","tilt_deg":25,"az_deg":180,"size_m":[11.0,6.0],"setbacks_m":0.5},
                depends_on=["pv_select_components"], layer=layer),
            PlanTask(
                id="mech_racking_layout",
                title="Place modules on surface",
                args={"surface":"R1","module_size_m":[1.14,1.72],"row_spacing_m":0.02},
                depends_on=["mech_surface"], layer=layer),
            PlanTask(
                id="mech_attachment_check",
                title="Check attachment spans & counts",
                args={"surface":"R1","max_span_m":1.8,"edge_clear_m":0.3},
                depends_on=["mech_racking_layout"], layer=layer),
            PlanTask(
                id="pv_stringing_plan",
                title="Compute stringing across MPPTs (series/parallel)",
                args={"layer": layer, "target_kw": kw},
                depends_on=["pv_select_components","mech_racking_layout"],
                layer=layer,
            ),
            PlanTask(
                id="pv_apply_stringing",
                title="Apply stringing (create DC links to MPPT terminals)",
                args={"layer": layer},
                depends_on=["pv_stringing_plan"],
                layer=layer,
            ),
            PlanTask(
                id="pv_add_disconnects",
                title="Add required DC/AC disconnects",
                args={"layer": layer, "jurisdiction_profile": "NEC_2023"},
                depends_on=["pv_apply_stringing"],
                layer=layer,
            ),
            PlanTask(
                id="pv_size_protection",
                title="Size OCPD/fusing per NEC 690",
                args={"layer": layer, "profile": "NEC_2023"},
                depends_on=["pv_add_disconnects"],
                layer=layer,
            ),
            PlanTask(
                id="pv_size_conductors",
                title="Size DC/AC conductors with derates and voltage-drop budgets",
                args={"layer": layer, "dc_vdrop_pct": 2.0, "ac_vdrop_pct": 3.0},
                depends_on=["pv_size_protection"],
                layer=layer,
            ),
            PlanTask(
                id="pv_generate_wiring",
                title="Auto-route links & create bundles/routes",
                args={"layer": layer},
                depends_on=["pv_size_conductors"],
                layer=layer,
            ),
            PlanTask(
                id="pv_compliance_check",
                title="Compliance check (blocking if non-conforming)",
                args={"layer": layer, "profile": "NEC_2023"},
                depends_on=["pv_generate_wiring"],
                layer=layer,
                risk="medium",
            ),
            PlanTask(
                id="pv_compute_bom",
                title="Compute BOM and cost summary",
                args={"layer": layer},
                depends_on=["pv_compliance_check"],
                layer=layer,
            ),
            PlanTask(
                id="pv_explain",
                title="Explain the design (homeowner + engineer views)",
                args={"layer": layer},
                depends_on=["pv_compute_bom"],
                layer=layer,
            ),
        ]

        plan = LongPlan(session_id=session_id, layer=layer, tasks=tasks, profile="NEC_2023")
        return LongPlanCard(title="PV Design Long Plan", plan=plan)
