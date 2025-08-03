"""Agent for sourcing alternative components based on price and availability.

The SourcingAgent helps users find cheaper or alternative components
within the same category.  Given a natural‑language request like
``find cheaper inverter`` or ``suggest alternatives for panel``, it
queries the component master database for items in the specified
category and returns a list of the lowest‑priced options along with
basic metadata.  This agent currently focuses on simple price
comparisons; future versions could incorporate lead times, regional
compliance and performance matching.
"""
from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType
from backend.services.component_db_service import get_component_db_service


@register
class SourcingAgent(AgentBase):
    """Suggest alternative components based on price and availability.

    This agent inspects the user's command to identify a component
    category (e.g. inverter, panel, battery, pump or compressor).
    It then searches the component master database for items in that
    category that have a defined price, sorts them by price, and
    returns up to three of the lowest‑priced components along with
    their manufacturer, part number, power rating and unit price.
    If no priced items exist in the chosen category or the category
    cannot be inferred from the command, the agent returns a helpful
    validation message.
    """

    name = "sourcing_agent"
    description = "Recommends alternative components based on price and availability."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        text = command.lower()
        # Determine the category referenced in the command
        category: str | None = None
        for cat in ["inverter", "panel", "battery", "pump", "compressor"]:
            if cat in text:
                category = cat
                break
        if category is None:
            msg = (
                "I couldn't determine which component category to search. "
                "Try commands like 'find cheaper inverter' or 'suggest alternatives for panels'."
            )
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": msg},
                    version=1,
                ).model_dump()
            ]

        # Query the database for items in this category
        async for svc in get_component_db_service():
            results = await svc.search(category=category)
            break
        # Filter to only those with a defined price and sort ascending
        priced = [c for c in results if c.price is not None]
        if not priced:
            msg = f"No components with pricing were found in category '{category}'."
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": msg},
                    version=1,
                ).model_dump()
            ]
        priced.sort(key=lambda c: c.price)
        top = priced[:3]
        # Build a list of human‑readable lines for the response
        lines: List[str] = []
        for comp in top:
            power = f"{comp.power:g} W" if comp.power is not None else "N/A"
            price = f"${comp.price:.2f}" if comp.price is not None else "N/A"
            lines.append(f"- {comp.manufacturer} {comp.part_number} ({power}, {price})")
        msg = (
            f"Here are the lowest‑priced {category}(s) I found:\n" + "\n".join(lines)
        )
        return [
            AiAction(
                action=AiActionType.validation,
                payload={"message": msg},
                version=1,
            ).model_dump()
        ]


# instantiate the agent
sourcing_agent = register(SourcingAgent())

