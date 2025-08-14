"""Simple consensus engine for aggregating agent proposals."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ConsensusEngine:
    """Combine multiple proposals and select a winner.

    The current implementation is intentionally naive: it selects the
    proposal with the highest ``confidence`` value.  If confidences are
    missing or equal, the first proposal is returned.  ``weights`` can
    be supplied to influence future more sophisticated scoring.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or {}

    def decide(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not proposals:
            return {}
        # Prefer proposal with highest confidence
        def score(p: Dict[str, Any]) -> float:
            return float(p.get("confidence", 0))

        return max(proposals, key=score)
