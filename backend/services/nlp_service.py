"""Utility functions for natural-language parsing.

This module offers helper functions to extract structured hints from
free-text commands.  It is intentionally lightweight, relying on simple
regular-expression heuristics rather than heavyweight NLP models.  The
current implementation supports:

* ``target_power`` – Power requirement in watts or kW (e.g. ``5 kW``,
  ``3000w``). kW values are normalised to watts.
* ``panel_count`` – Explicit number of panels in phrases like
  "add 6 panels".
* ``domain`` – Rough domain classification based on keywords, such as
  ``pv`` for solar-related terms or ``hvac`` for heating/cooling.

The parser should be extended or replaced with a robust NLP/LLM
approach as OriginFlow evolves.
"""

from __future__ import annotations

import re
from typing import Any, Dict


_POWER_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(k\s*w|kw|w)\b")
_PANEL_RE = re.compile(r"(\d+)\s*panels?")


def parse_command(command: str) -> Dict[str, Any]:
    """Parse a user command into structured fields.

    Parameters
    ----------
    command:
        Raw user input (e.g. "Design a 5kW solar system").

    Returns
    -------
    dict
        Mapping of extracted keys to values.  Unknown values are omitted.
    """
    result: Dict[str, Any] = {}
    if not command:
        return result

    cmd = command.lower().strip()

    # Power requirement (e.g. "5kW", "5000 w")
    power_match = _POWER_RE.search(cmd)
    if power_match:
        value = float(power_match.group(1))
        unit = power_match.group(2).replace(" ", "")
        if unit.startswith("k"):
            value *= 1000
        result["target_power"] = value

    # Explicit panel count (e.g. "add 6 panels")
    panel_match = _PANEL_RE.search(cmd)
    if panel_match:
        try:
            result["panel_count"] = int(panel_match.group(1))
        except ValueError:
            pass

    # Keyword-based domain inference
    if any(word in cmd for word in ["solar", "pv", "panel", "inverter"]):
        result["domain"] = "pv"
    elif any(word in cmd for word in ["hvac", "heat", "cool", "air"]):
        result["domain"] = "hvac"
    elif any(word in cmd for word in ["pump", "water", "irrigation"]):
        result["domain"] = "water"

    return result
