"""Minimal agent that summarises required component categories."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType


@register
class SystemDesignAgent(AgentBase):
    """Provides high-level system design suggestions."""

    name = "system_design_agent"
    description = "Outlines major components for a project."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        text = command.lower()
        if "solar" in text or "pv" in text:
            size_match = re.search(r"(\d+(?:\.\d+)?)\s*kw", text)
            size = size_match.group(1) if size_match else None
            size_str = f" of around {size} kW" if size else ""
            message = (
                f"To design a solar PV system{size_str}, you need panels, an inverter, batteries (optional), a charge controller and BOS items."
            )
        elif any(word in text for word in ["hvac", "air"]):
            message = (
                "For an HVAC system you will need compressor/condenser, evaporator coil, ductwork or piping, and control systems."
            )
        elif "pump" in text or "water" in text:
            message = (
                "For a water pumping system you will need a suitable pump, piping, power source and control/safety devices."
            )
        else:
            message = (
                "I'm not sure which domain you're working in. Specify solar, HVAC or water pumping."
            )
        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]
