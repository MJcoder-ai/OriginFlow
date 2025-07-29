"""Agent that sizes wires, connectors, and protection devices.

In future versions this agent will integrate with the deterministic rule
engine to compute wire gauges, fuse sizes and connectors based on load,
distance and applicable standards.  Currently it acts as a placeholder to
demonstrate the agent architecture.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType
from backend.services.rule_engine import default_rule_engine


@register
class WiringAgent(AgentBase):
    """Placeholder wiring agent."""

    name = "wiring_agent"
    description = "Sizes wires and connectors (stub)."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Size wires and protection devices based on load and distance.

        The command should contain a numeric power (in kW) and a distance (in metres).
        Example: "size wiring for 5 kW over 20 m".  If either value is missing
        or cannot be parsed, the agent returns a helpful message.
        """
        text = command.lower()
        # Try to extract a power in kW
        load_kw: Optional[float] = None
        distance_m: Optional[float] = None
        import re

        kw_match = re.search(r"(\d+(?:\.\d+)?)\s*kw", text)
        if kw_match:
            try:
                load_kw = float(kw_match.group(1))
            except ValueError:
                load_kw = None

        dist_match = re.search(r"(\d+(?:\.\d+)?)\s*m", text)
        if dist_match:
            try:
                distance_m = float(dist_match.group(1))
            except ValueError:
                distance_m = None

        if load_kw is None or distance_m is None:
            message = (
                "To size wiring please specify both the load (in kW) and the cable run length (in m), e.g. 'size wiring for 5 kW over 20 m'."
            )
            action = AiAction(
                action=AiActionType.validation,
                payload={"message": message},
                version=1,
            ).model_dump()
            return [action]

        # Use the rule engine to compute the wire size
        result = default_rule_engine.size_wire(load_kw=load_kw, distance_m=distance_m)
        message = (
            f"For a load of {load_kw:g}\xa0kW over {distance_m:g}\xa0m: "
            f"use {result.gauge} copper wire (cross-section {result.cross_section_mm2:g}\xa0mm\xb2).\n"
            f"Calculated current: {result.current_a:.1f}\xa0A; voltage drop \u2248 {result.voltage_drop_pct:.2f}\xa0%; "
            f"recommended fuse rating: {result.fuse_rating_a:.1f}\xa0A."
        )
        action = AiAction(
            action=AiActionType.validation,
            payload={"message": message},
            version=1,
        ).model_dump()
        return [action]
