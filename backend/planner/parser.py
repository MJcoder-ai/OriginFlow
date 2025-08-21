"""
Rule-based parser for NL design commands.

This module extracts the minimal quantities needed to drive the orchestrator:
 - target size in kW
 - assumed panel wattage
 - number of panels (rounded up)
 - design layer
It avoids any model calls for reliability and testability.
"""
import re
import math
from typing import Any, Dict
from .schemas import ParsedPlan

KW_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kW|kw|KW)\b")
WATT_RE = re.compile(r"(\d{3,4})\s*(W|w)\b")
LAYER_HINT_RE = re.compile(r"(single[-\s]?line|electrical)", re.IGNORECASE)

DEFAULT_KW = 5.0
DEFAULT_PANEL_W = 400
DEFAULT_LAYER = "electrical"


def _extract_kw(text: str) -> float:
    m = KW_RE.search(text)
    if not m:
        return DEFAULT_KW
    try:
        return float(m.group(1))
    except Exception:
        return DEFAULT_KW


def _extract_panel_watts(text: str) -> int:
    # Heuristic: when the command mentions a wattage and mentions panel/module,
    # prefer that as the panel rating. Otherwise, default.
    if "panel" in text.lower() or "module" in text.lower():
        m = WATT_RE.search(text)
        if m:
            try:
                watts = int(m.group(1))
                # sanity clamp: typical residential panel is ~350–500W
                if 250 <= watts <= 700:
                    return watts
            except Exception:
                pass
    return DEFAULT_PANEL_W


def _extract_layer(text: str) -> str:
    m = LAYER_HINT_RE.search(text)
    if not m:
        return DEFAULT_LAYER
    val = m.group(1).lower().replace(" ", "-")
    return "single-line" if "single" in val else "electrical"


def parse_design_command(command: str) -> ParsedPlan:
    """
    Parse a design request like "design a 5kW solar PV system" into
    deterministic quantities used to produce a plan.
    """
    text = command or ""
    target_kw = _extract_kw(text)
    panel_watts = _extract_panel_watts(text)
    layer = _extract_layer(text)

    target_watts = target_kw * 1000.0
    panel_count = max(1, math.ceil(target_watts / float(panel_watts)))

    assumptions: Dict[str, Any] = {
        "defaulted_target_kw": target_kw == DEFAULT_KW and KW_RE.search(text) is None,
        "defaulted_panel_watts": panel_watts == DEFAULT_PANEL_W and WATT_RE.search(text) is None,
        "defaulted_layer": layer == DEFAULT_LAYER and LAYER_HINT_RE.search(text) is None,
    }

    return ParsedPlan(
        target_kw=target_kw,
        panel_watts=panel_watts,
        panel_count=panel_count,
        layer=layer,
        assumptions=assumptions,
    )
