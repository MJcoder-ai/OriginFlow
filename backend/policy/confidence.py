from dataclasses import dataclass
from typing import Dict

from backend.schemas.ai import AiActionType


@dataclass
class ConfidenceThresholds:
    auto_approve_min: float
    human_review_min: float


DEFAULT_THRESHOLDS: Dict[str, ConfidenceThresholds] = {
    "design": ConfidenceThresholds(auto_approve_min=0.82, human_review_min=0.55),
    "wiring": ConfidenceThresholds(auto_approve_min=0.85, human_review_min=0.60),
    "bom":    ConfidenceThresholds(auto_approve_min=0.80, human_review_min=0.50),
}


ACTION_DOMAIN: Dict[AiActionType, str] = {
    AiActionType.add_component: "design",
    AiActionType.remove_component: "design",
    AiActionType.add_link: "wiring",
    AiActionType.remove_link: "wiring",
    # Extend as needed
}


def get_thresholds_for_action(action_type: AiActionType) -> ConfidenceThresholds:
    """Return per-action confidence thresholds.

    Validation actions carry important instructions (e.g. upload missing
    datasheets) and should never be auto-approved. We therefore set an
    unreachable auto-approval threshold for AiActionType.validation.
    """
    if action_type == AiActionType.validation:
        # Force manual review: auto_approve_min > 1.0 ensures no auto-approval
        return ConfidenceThresholds(auto_approve_min=2.0, human_review_min=0.0)
    domain = ACTION_DOMAIN.get(action_type, "design")
    return DEFAULT_THRESHOLDS.get(domain, DEFAULT_THRESHOLDS["design"])
