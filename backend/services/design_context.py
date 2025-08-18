from __future__ import annotations
from typing import Dict, List, Optional

from backend.schemas.analysis import DesignSnapshot
from backend.schemas.analysis import CanvasComponent


def _base_class_of(comp_type: str) -> str:
    t = comp_type.lower()
    if "panel" in t or "module" in t:
        return "panel"
    if "inverter" in t:
        return "inverter"
    if "battery" in t:
        return "battery"
    if "meter" in t or "ct" in t:
        return "meter"
    if "controller" in t or "mppt" in t:
        return "controller"
    if "combiner" in t:
        return "combiner"
    if "optimizer" in t:
        return "optimizer"
    if "disconnect" in t or "isolator" in t:
        return "disconnect"
    return "unknown"


def inventory_counts(components: List[CanvasComponent]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for c in components:
        b = _base_class_of(c.type)
        counts[b] = counts.get(b, 0) + 1
    return counts


def requirement_estimates(snapshot: Optional[DesignSnapshot]) -> Dict[str, Optional[float]]:
    out = {
        "panel_count_estimate": None,
        "inverter_count_estimate": None,
        "target_power_kw": None,
    }
    if snapshot is None:
        return out
    meta = getattr(snapshot, "metadata", {}) or {}
    req = meta.get("requirements") or {}
    out["panel_count_estimate"] = req.get("panel_count_estimate")
    out["inverter_count_estimate"] = req.get("inverter_count_estimate")
    out["target_power_kw"] = req.get("target_power") or req.get("target_power_kw")
    return out


def priors_for_next_step(snapshot: Optional[DesignSnapshot]) -> Dict[str, float]:
    if snapshot is None:
        return {}
    counts = inventory_counts(snapshot.components)
    req = requirement_estimates(snapshot)

    priors: Dict[str, float] = {}
    for cls_key, est_key in [("panel","panel_count_estimate"), ("inverter","inverter_count_estimate")]:
        est = req.get(est_key)
        if isinstance(est, (int, float)):
            have = counts.get(cls_key, 0)
            if est > have:
                priors[f"add_component.{cls_key}"] = 0.7
    return priors
