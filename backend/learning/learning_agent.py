"""Learning agent for calibration and feedback aggregation."""
from __future__ import annotations

from typing import Any, Dict, List


class LearningAgent:
    """Very small learning component storing envelopes in memory."""

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    async def update(self, session_id: str, envelope: Dict[str, Any]) -> None:
        """Record an envelope for later analysis."""
        self._records.append({"session_id": session_id, "envelope": envelope})

    def history(self) -> List[Dict[str, Any]]:
        return list(self._records)
