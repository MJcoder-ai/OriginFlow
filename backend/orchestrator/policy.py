"""
Risk policy and decisions for orchestrated actions.

This simple policy classifies tasks into risk classes and returns a decision:
- 'auto'            → orchestrator may apply the patch immediately
- 'review_required' → the patch must be presented for human approval
- 'blocked'         → do not produce a patch; return guidance instead

In Phase 6 we will extend this with confidence calibration and approvals.
"""
from __future__ import annotations

from typing import Literal

Decision = Literal["auto", "review_required", "blocked"]
Risk = Literal["low", "medium", "high"]


TASK_RISK: dict[str, Risk] = {
    # safe: adds wiring edges in the current view
    "generate_wiring": "low",
    # medium: adds structural nodes/edges
    "generate_mounts": "medium",
    # low: adds a monitoring node and data links
    "add_monitoring": "low",
    # low: adds placeholders (reversible)
    "make_placeholders": "low",
    # replacement mutates existing nodes → review by default (tunable in Phase 6)
    "replace_placeholders": "medium",
}


def decide(task: str, confidence: float | None = None) -> Decision:
    """Return decision for a task based on static risk and optional confidence."""
    risk = TASK_RISK.get(task, "medium")
    # Simple rule-set; extend later with calibrated confidence + user/org policy:
    if risk == "low":
        return "auto"
    if risk == "medium":
        return "review_required"
    return "blocked"
