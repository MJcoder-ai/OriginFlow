from __future__ import annotations
import re
from typing import Dict, Any
from pydantic import Field
from backend.tools.schemas import ToolBase, make_patch
from backend.odl.schemas import PatchOp

DEFAULT_ENV = {"site_tmin_C": -10.0, "site_tmax_C": 45.0, "utility": "120/240V", "profile": "NEC_2023"}
DEFAULT_TARGETS = {"vd_dc_pct": 2.0, "vd_ac_pct": 3.0}
DEFAULT_CONSTRAINTS = {"bus_A": 200, "main_A": 200, "interconnection": "load_side"}
DEFAULT_PREFS = {"optimizer": "cost", "mlpe": "auto"}


class NLToPlanSpecInput(ToolBase):
    utterance: str
    # Optional tenant defaults may be passed from chat if available
    defaults: Dict[str, Any] = Field(default_factory=dict)


_KW = re.compile(r"(?P<val>\d+(\.\d+)?)\s*(k\s*w\s*p?|kwp|kw|kilowatt(?:s)?)", re.I)
_PROFILE = re.compile(r"\b(NEC\s*20(1\d|2\d)|IEC\s*60364)\b", re.I)
_UTIL = re.compile(r"(120/240|230|400/230|415|480)\s*v", re.I)


def _num(m):
    try:
        return float(m.group("val"))
    except Exception:
        return None


def parse_plan_spec(inp: NLToPlanSpecInput) -> Dict[str, Any]:
    """Parse a natural-language request into a PlanSpec dict and patch.

    Returns a dictionary with:
    - ``spec``: a PlanSpec-compatible dictionary
    - ``patch``: an :class:`ODLPatch` that stores the spec in meta and adds an
      annotation edge for traceability
    """

    t = inp.utterance.strip().lower()
    # 1) targets.dc_kw_stc
    m = _KW.search(t)
    dc_kw = _num(m) if m else 3.0
    # 2) profile / utility (optional)
    prof = _PROFILE.search(t)
    util = _UTIL.search(t)
    env = {
        "site_tmin_C": inp.defaults.get("site_tmin_C", DEFAULT_ENV["site_tmin_C"]),
        "site_tmax_C": inp.defaults.get("site_tmax_C", DEFAULT_ENV["site_tmax_C"]),
        "utility": util.group(0).upper().replace(" ", "")
        if util
        else inp.defaults.get("utility", DEFAULT_ENV["utility"]),
        "profile": prof.group(0).replace(" ", "_").upper()
        if prof
        else inp.defaults.get("profile", DEFAULT_ENV["profile"]),
    }
    spec = {
        "scope": "pv_resi_grid_tied",
        "env": env,
        "targets": {"dc_kw_stc": dc_kw, **DEFAULT_TARGETS},
        "constraints": {**DEFAULT_CONSTRAINTS, **inp.defaults.get("constraints", {})},
        "preferences": {**DEFAULT_PREFS, **inp.defaults.get("preferences", {})},
        "inputs_optional": inp.defaults.get("inputs_optional", {}),
    }

    ops = [
        PatchOp(
            op_id=f"{inp.request_id}:meta:plan_spec",
            op="set_meta",
            value={"path": "design_state.plan_spec", "merge": True, "data": spec},
        ),
        PatchOp(
            op_id=f"{inp.request_id}:ann:plan_spec",
            op="add_edge",
            value={
                "id": f"ann:plan_spec:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "parse_plan_spec",
                    "summary": f"Parsed target {dc_kw:.2f} kW, env={env['utility']}/{env['profile']}",
                },
            },
        ),
    ]

    return {"spec": spec, "patch": make_patch(inp.request_id, ops)}
