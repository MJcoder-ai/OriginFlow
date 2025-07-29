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
from fastapi import HTTPException

from backend.services.hierarchical_component_service import (
    HierarchicalComponentService,
    get_hierarchical_component_service,
)


@register
class InventoryAgent(AgentBase):
    """Searches the component master database for suitable components."""

    name = "inventory_agent"
    description = "Looks up components and suggests options based on category and ratings."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Handle inventory search requests.

        This method supports searching for components across multiple domains
        using the hierarchical component service.  The command can specify a
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

        domain_map = {
            "panel": "PV",
            "inverter": "PV",
            "battery": "PV",
            "controller": "PV",
            "pump": "Water",
            "compressor": "HVAC",
        }
        domain = domain_map.get(category, None)

        async for svc in get_hierarchical_component_service():
            results = await svc.search(domain=domain)
            break

        if min_power is not None:
            filtered = []
            for comp in results:
                attrs = comp.attributes or {}
                variant_specific = attrs.get("variant_specific", {})
                power = variant_specific.get("power_w") or attrs.get("power") or None
                if power is None:
                    continue
                try:
                    pw = float(power)
                    if pw >= min_power:
                        filtered.append(comp)
                except Exception:
                    continue
            results = filtered

        if not results:
            message = f"No {category} components found."
        else:
            lines = [f"Found {len(results)} {category}(s):"]
            for comp in results[:5]:
                attrs = comp.attributes or {}
                variant_specific = attrs.get("variant_specific", {})
                power = variant_specific.get("power_w") or attrs.get("power")
                trust = comp.trust_level
                region_list = comp.available_regions or []
                region_str = ",".join(region_list) if region_list else "Global"
                lines.append(
                    f"- {comp.brand} {comp.mpn or 'N/A'} ({power or 'N/A'}W, trust={trust}, regions={region_str})"
                )
            message = "\n".join(lines)

        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]

