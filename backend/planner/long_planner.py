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

        tasks = [
            PlanTask(
                id="select_equipment",
                title="Select inverter + module",
                args={"target_kw_stc": kw, "preferred_module_W": module_w},
                layer=layer,
                rationale=rationale,
            ),
            PlanTask(
                id="select_dc_stringing",
                title="Compute stringing plan",
                args={"target_kw_stc": kw},
                layer=layer,
                depends_on=["select_equipment"],
            ),
            PlanTask(
                id="make_placeholders",
                title="Add placeholders",
                args={"component_type": "panel", "count": panel_count, "layer": layer},
                layer=layer,
                depends_on=["select_dc_stringing"],
            ),
            PlanTask(
                id="select_ocp_dc",
                title="Size DC protection",
                args={"layer": layer},
                depends_on=["make_placeholders"],
            ),
            PlanTask(
                id="select_conductors_v2",
                title="Size conductors",
                args={"layer": layer},
                depends_on=["select_ocp_dc"],
            ),
            PlanTask(
                id="generate_wiring",
                title="Generate wiring",
                args={"layer": layer},
                depends_on=["select_conductors_v2"],
            ),
            PlanTask(
                id="check_compliance_v2",
                title="Compliance check",
                args={"layer": layer},
                depends_on=["generate_wiring"],
            ),
            PlanTask(
                id="generate_bom",
                title="Compute BOM",
                args={"layer": layer},
                depends_on=["check_compliance_v2"],
            ),
        ]

        plan = LongPlan(session_id=session_id, layer=layer, tasks=tasks, profile="NEC_2023")
        return LongPlanCard(title="PV Design Long Plan", plan=plan)
