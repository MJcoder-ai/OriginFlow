"""
Risk-based policy engine for OriginFlow governance.

This module implements a simple decision engine that determines whether
an AI action may be automatically approved based on the originating
agent's risk class and the action's confidence score.  Risk classes
(``low``, ``medium`` and ``high``) correspond to escalating levels of
manual oversight:

* ``low`` risk actions are auto-approved regardless of confidence.
* ``medium`` risk actions require a minimum confidence threshold to be
  considered safe; below this threshold a human should review the action.
* ``high`` risk actions always require human approval; no amount of
  confidence can bypass review.

Future implementations may load thresholds and policies from configuration
or per-tenant settings.  See the Phase 8 documentation for details.
"""
from __future__ import annotations

from typing import Optional

from backend.agents.registry import get_spec
from backend.schemas.ai import AiActionType


class RiskPolicy:
    """Risk-based policy helper to decide auto-approval status."""

    # Thresholds for auto-approval per risk class.  Values represent the
    # minimum confidence required to allow automatic execution.  High risk
    # actions have a threshold above 1.0 so they can never auto-approve.
    RISK_THRESHOLDS = {
        "low": 0.0,
        "medium": 0.75,
        "high": 1.1,
    }

    @classmethod
    def is_auto_approved(
        cls,
        agent_name: str,
        action_type: AiActionType,
        confidence: Optional[float],
    ) -> bool:
        """
        Decide whether an action from ``agent_name`` with the given
        confidence should be automatically approved.

        Args:
            agent_name: Name of the agent that produced the action.
            action_type: The type of action being considered (currently
                unused but reserved for future granular policies).
            confidence: Confidence score assigned to the action.  If
                ``None`` a default of 0.0 is assumed.

        Returns:
            ``True`` if the action should be auto-approved based on the
            agent's risk class and confidence; ``False`` otherwise.
        """
        conf = float(confidence or 0.0)
        try:
            spec = get_spec(agent_name)
            risk = spec.risk_class or "medium"
        except Exception:
            # Default to medium risk if the spec cannot be retrieved
            risk = "medium"
        threshold = cls.RISK_THRESHOLDS.get(risk, cls.RISK_THRESHOLDS["high"])
        return conf >= threshold
