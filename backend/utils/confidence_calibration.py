"""
Confidence calibration utilities for adaptive AI action scoring.

This module introduces a lightweight `ConfidenceCalibrator` that adjusts
agent confidence scores based on historical user feedback.  When a user
approves or rejects actions produced by an agent, the calibrator records
the outcome and uses it to refine future confidence estimates.  By
calibrating confidence scores, the system can tailor its auto‑approval
thresholds and better align with user expectations over time.

The calibration strategy implemented here is intentionally simple.  It
computes an acceptance rate for each `(agent_name, action_type)` pair
and scales new confidence values towards or away from the mid‑point (0.5)
depending on the acceptance history.  More sophisticated approaches
could incorporate confidence distributions, Bayesian updates or neural
calibrators, but this implementation is sufficient for demonstration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class FeedbackRecord:
    """Record of an approval or rejection decision for calibration."""

    agent_name: str
    action_type: str
    confidence: float
    approved: bool


class ConfidenceCalibrator:
    """Adaptive calibrator for agent confidence scores."""

    def __init__(self) -> None:
        # Store feedback history keyed by (agent_name, action_type)
        self._records: Dict[Tuple[str, str], List[FeedbackRecord]] = {}

    def record_feedback(
        self,
        *,
        agent_name: str,
        action_type: str,
        confidence: float,
        approved: bool,
    ) -> None:
        """Record a user approval or rejection for a given action.

        Args:
            agent_name: Name of the agent that produced the action.
            action_type: Type of the action (string identifier).
            confidence: Confidence score assigned to the action.
            approved: ``True`` if the user approved the action, ``False`` if rejected.
        """
        key = (agent_name, action_type)
        rec = FeedbackRecord(agent_name, action_type, confidence, approved)
        self._records.setdefault(key, []).append(rec)

    def _acceptance_rate(self, agent_name: str, action_type: str) -> float:
        """Compute the fraction of approved actions for a given agent and action type."""
        key = (agent_name, action_type)
        records = self._records.get(key)
        if not records:
            return 0.5  # neutral acceptance rate for unseen actions
        approved_count = sum(1 for r in records if r.approved)
        return approved_count / len(records)

    def calibrate_confidence(
        self,
        *,
        agent_name: str,
        action_type: str,
        original_confidence: float,
    ) -> float:
        """Adjust a confidence score based on historical feedback.

        The calibrated confidence is biased towards 0.5 (neutral) when the
        acceptance rate is low and towards the original value when it is high.
        This behaviour means the system becomes more conservative if many
        proposals are rejected and more trusting if most are accepted.

        Args:
            agent_name: Name of the agent producing the score.
            action_type: Type of the action.
            original_confidence: Raw confidence score (0.0 to 1.0).

        Returns:
            A calibrated confidence score between 0 and 1.
        """
        rate = self._acceptance_rate(agent_name, action_type)
        # Blend the original confidence with the mid‑point based on acceptance rate
        # When rate=1: return original_confidence; when rate=0: return 0.5
        return original_confidence * rate + 0.5 * (1.0 - rate)

    def get_threshold(self, agent_name: str, action_type: str, base_threshold: float) -> float:
        """Compute a dynamic auto‑approval threshold for an action type.

        The threshold is scaled according to the acceptance rate.  If most
        actions are accepted, the threshold decreases slightly (making
        auto‑approval more likely); if many actions are rejected, the
        threshold increases (making auto‑approval harder).  Thresholds are
        clamped to the range [0.5, 0.95].

        Args:
            agent_name: Name of the agent.
            action_type: Action type.
            base_threshold: The default threshold defined by the governance policy.

        Returns:
            A calibrated threshold between 0.5 and 0.95.
        """
        rate = self._acceptance_rate(agent_name, action_type)
        # Scale threshold: more acceptance lowers threshold, less raises it
        # Example: rate=1 -> threshold * 0.9; rate=0 -> threshold * 1.1
        factor = 1.0 + (0.1 * (0.5 - rate))
        dynamic_threshold = base_threshold * factor
        # Clamp
        return max(0.5, min(0.95, dynamic_threshold))
