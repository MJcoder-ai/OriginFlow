"""Agent for searching the component master database."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType
from backend.services.component_db_service import get_component_db_service


@register
class InventoryAgent(AgentBase):
    """Suggest components from the master database."""

    name = "inventory_agent"
    description = "Looks up components in the master database."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        pattern = re.compile(r"(panel|inverter|battery|controller)(?:\s+(\d+))?", re.IGNORECASE)
        match = pattern.search(command)
        if not match:
            return []
        category = match.group(1).lower()
        power = float(match.group(2)) if match.group(2) else None

        async for service in get_component_db_service():
            results = await service.search(category=category, min_power=power)
            break

        if not results:
            message = f"No components found for category '{category}'."
        else:
            lines = [f"Found {len(results)} {category}(s):"]
            for comp in results[:5]:
                price = f"${comp.price:.2f}" if comp.price is not None else "N/A"
                lines.append(
                    f"- {comp.manufacturer} {comp.part_number} ({comp.power or 'N/A'}W, {price})"
                )
            message = "\n".join(lines)

        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]
