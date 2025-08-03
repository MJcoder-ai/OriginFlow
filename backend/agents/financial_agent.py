from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType


@register
class FinancialAgent(AgentBase):
    """Provides rough cost estimates for systems."""

    name = "financial_agent"
    description = "Rough cost estimation for common systems (stub)."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        text = command.lower()
        m = re.search(r"(\d+(?:\.\d+)?)\s*(kw|kilowatt)", text)
        if not m:
            message = "Please specify a system size in kW for cost estimation."
        else:
            try:
                size_kw = float(m.group(1))
                cost = size_kw * 1000.0
                message = f"Estimated cost for a {size_kw:g} kW system is roughly ${cost:,.0f}."
            except ValueError:
                message = "Unable to parse the system size."
        action = AiAction(
            action=AiActionType.validation,
            payload={"message": message},
            version=1,
        ).model_dump()
        return [action]


financial_agent = register(FinancialAgent())
