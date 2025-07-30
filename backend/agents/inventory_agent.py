"""Agent responsible for retrieving components from the master database.

This agent exposes simple search functionality over the component master database.  It is used by
the SystemDesignAgent to find suitable components based on category, rating, manufacturer or
cost.  In Phase\xa01 it returns a human-readable report summarising the available options.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType

from backend.services.component_db_service import (
    ComponentDBService,
    get_component_db_service,
)


@register
class InventoryAgent(AgentBase):
    """Searches the component master database for suitable components."""

    name = "inventory_agent"
    description = "Looks up components and suggests options based on category and ratings."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Handle inventory search requests.

        This method searches the component master table via
        :class:`ComponentDBService`. The command can specify a
        category (panel, inverter, battery, controller, pump, compressor) and
        an optional minimum power rating.  In future revisions, users will
        also be able to filter by trust level and region (e.g., "trust>=2",
        "region=EU").
        """
        text = command.lower()
        pattern = re.compile(
            r"(?P<category>panel|inverter|battery|controller|pump|compressor)"  # component type
            r"(?:\s+(?P<power>\d+(?:\.\d+)?))?",
            re.IGNORECASE,
        )
        m = pattern.search(text)
        if not m:
            return []

        category = m.group("category").lower()
        power_str = m.group("power")
        min_power: float | None = None
        if power_str:
            try:
                min_power = float(power_str)
            except ValueError:
                min_power = None

        async for svc in get_component_db_service():
            results = await svc.search(category=category, min_power=min_power)
            break

        if not results:
            # Provide guidance to the user when no results are returned.
            power_hint = f" {min_power:g}W" if min_power else ""
            message = (
                f"I couldn't find a '{category}{power_hint}' in the database. "
                "You can upload a datasheet to add a new component or try a different query."
            )
        else:
            lines = [f"Found {len(results)} {category}(s):"]
            for comp in results[:5]:
                power = comp.power
                lines.append(
                    f"- {comp.manufacturer} {comp.part_number} ({power or 'N/A'}W)"
                )
            message = "\n".join(lines)

        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]


# instantiate the agent so the registry stores an instance
inventory_agent = register(InventoryAgent())

