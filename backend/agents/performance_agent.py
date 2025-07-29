"""Agent stub for rough system performance estimations."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType


@register
class PerformanceAgent(AgentBase):
    """Estimates overall system performance (placeholder)."""

    name = "performance_agent"
    description = "Estimates annual energy yield or efficiency (stub)."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        message = (
            "Performance estimation is not yet available. "
            "Future versions will integrate simulation tools to provide yield predictions."
        )
        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]

