"""Agent orchestrating high-level system design requests (Phase\xa01 minimal).

In Phase\xa01 this agent simply recognises high-level project requirements and
returns a plain language overview of the major component types required.
Future versions will perform task decomposition and orchestrate specialist
agents to assemble a full design.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType


@register
class SystemDesignAgent(AgentBase):
    """High\u2011level system design agent.

    This agent interprets a user's high\u2011level project request, determines the
    engineering domain (solar PV, HVAC, or water pumping) and extracts any
    specified system size (e.g., kilowatts or tons).  It responds with a
    concise overview of the major component categories required, provides
    rough sizing hints and suggests logical next steps such as searching for
    available components or fetching datasheets.  Future versions will
    orchestrate specialist agents to create detailed designs.
    """

    name = "system_design_agent"
    description = (
        "Produces a high\u2011level overview of required components and next steps based on the project domain and capacity."
    )

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        text = command.lower()
        size_kw: float | None = None
        size_desc = ""
        kw_match = re.search(r"(\d+(?:\.\d+)?)\s*(kw|kilowatt)", text)
        ton_match = re.search(r"(\d+(?:\.\d+)?)\s*(ton|tons)", text)
        if kw_match:
            try:
                size_kw = float(kw_match.group(1))
                size_desc = f" of around {size_kw:g}\xa0kW"
            except ValueError:
                size_kw = None
        elif ton_match:
            try:
                tons = float(ton_match.group(1))
                size_kw = tons * 3.517
                size_desc = f" sized for approximately {tons:g}\xa0ton"
            except ValueError:
                size_kw = None

        if any(word in text for word in ["solar", "pv"]):
            domain = "PV"
        elif any(word in text for word in ["air", "hvac", "ac"]):
            domain = "HVAC"
        elif any(word in text for word in ["pump", "water"]):
            domain = "Water"
        else:
            domain = None

        if domain == "PV":
            panel_hint = ""
            if size_kw:
                num_panels = int(round(size_kw * 1000 / 400.0))
                panel_hint = f" (~{num_panels} panels of ~400\xa0W)"
            message = (
                f"For a solar PV system{size_desc}, you'll need:\n"
                f"- Solar panels{panel_hint}.\n"
                f"- An inverter matched to the array power.\n"
                f"- A battery bank for storage (optional).\n"
                f"- A charge controller or BMS to manage charging.\n"
                f"- Balance-of-System (BOS) components: fuses, wires, connectors and mounting.\n\n"
                f"Next: ask me to search for panels (e.g., 'find panels 400') or fetch a datasheet for a specific part number."
            )
        elif domain == "HVAC":
            message = (
                f"For an HVAC system{size_desc}, the key components are:\n"
                f"- Compressor/condenser unit.\n"
                f"- Evaporator coil.\n"
                f"- Ductwork or piping sized for the required airflow or refrigerant.\n"
                f"- Thermostats and control systems.\n\n"
                f"You can ask me to find compressors or controllers based on your capacity and brand preferences."
            )
        elif domain == "Water":
            message = (
                f"For a water pumping system{size_desc}, you'll need:\n"
                f"- A pump selected for the desired flow rate and head.\n"
                f"- Piping, fittings and valves.\n"
                f"- A power source (electric motor, solar pump controller or engine).\n"
                f"- Control and safety devices (pressure switches, level sensors).\n\n"
                f"Next: request to find pumps or controllers to begin component selection."
            )
        else:
            message = (
                "I'm not sure which domain you're working in.  Please specify whether you're designing a solar, HVAC or water pumping system, and include the desired capacity (e.g., '5\xa0kW solar system')."
            )
        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]

