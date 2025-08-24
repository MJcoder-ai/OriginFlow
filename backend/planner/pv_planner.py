from __future__ import annotations
import math
from typing import Dict, Any, List
from .quantity import parse_pv_intent, clamp_count

# Reasonable defaults if the prompt omits details
DEFAULT_MODULE_WATTS = 400.0  # W per module
DEFAULT_INVERTER_QTY = 1

def _decide_counts(text: str) -> (int, int, List[str]):
    """
    Returns (inverter_qty, panel_qty, warnings)
    """
    intent = parse_pv_intent(text)
    warnings: List[str] = []

    inverter_qty = intent.inverter_qty if intent.inverter_qty else DEFAULT_INVERTER_QTY
    inverter_qty = clamp_count(inverter_qty, lo=1, hi=16)

    if intent.panel_qty:
        panel_qty = clamp_count(intent.panel_qty, lo=1, hi=1024)
    else:
        module_w = intent.module_watts or DEFAULT_MODULE_WATTS
        if intent.system_kw:
            target_w = intent.system_kw * 1000.0
            panel_qty = clamp_count(math.ceil(target_w / module_w), lo=2, hi=1024)
        else:
            panel_qty = 8
            warnings.append("No system size specified; defaulting panels=8 at ~400 W each.")

    if "400" in text and inverter_qty > 8 and panel_qty <= 20:
        warnings.append("Adjusted unrealistic inverter count that likely came from '400 W' modules text.")
        inverter_qty = DEFAULT_INVERTER_QTY

    return inverter_qty, panel_qty, warnings

def plan_pv_single_line(command_text: str) -> Dict[str, Any]:
    """
    Produce a minimal, correct plan for PV on the single-line layer:
      1) add one inverter placeholder (unless explicitly asked otherwise)
      2) add panels sized to system kW or default
      3) generate wiring
    """
    inv_qty, pan_qty, warns = _decide_counts(command_text or "")
    tasks = [
        {
            "id": "make_placeholders",
            "args": {"component_type": "inverter", "count": inv_qty, "layer": "single-line"},
        },
        {
            "id": "make_placeholders",
            "args": {"component_type": "panel", "count": pan_qty, "layer": "single-line"},
        },
        {
            "id": "generate_wiring",
            "args": {"layer": "single-line"},
        },
    ]
    return {"tasks": tasks, "warnings": warns}
