"""Agent for basic wiring size calculations (stub)."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType


@register
class WiringAgent(AgentBase):
    """Suggests wire sizes using simple heuristics."""

    name = "wiring_agent"
    description = "Estimates suitable wire sizes for given power and distance."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        message = (
            "Wire sizing calculations are not implemented yet. "
            "Assuming copper conductors and typical efficiency, please consult a qualified engineer."
        )
        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]

