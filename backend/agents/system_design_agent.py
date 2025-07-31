"""Agent orchestrating high-level system design requests (Phase\xa01 minimal).

In Phase\xa01 this agent simply recognises high-level project requirements and
returns a plain language overview of the major component types required.
Future versions will perform task decomposition and orchestrate specialist
agents to assemble a full design.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.utils.id import generate_id

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

        actions: List[Dict[str, Any]] = []

        if domain == "PV" and size_kw:
            num_panels = max(1, int(round(size_kw * 1000.0 / 400.0)))
            id_map: dict[str, str] = {}
            for i in range(num_panels):
                comp_id = generate_id("component")
                id_map[f"Panel {i + 1}"] = comp_id
                x_pos = 100 + (i % 4) * 120
                y_pos = 100 + (i // 4) * 120
                actions.append(
                    AiAction(
                        action=AiActionType.add_component,
                        payload={
                            "id": comp_id,
                            "name": f"Panel {i + 1}",
                            "type": "panel",
                            "standard_code": "PANEL-STD",
                            "x": x_pos,
                            "y": y_pos,
                            "layer": "Single-Line Diagram",
                        },
                        version=1,
                    ).model_dump()
                )
            inverter_id = generate_id("component")
            id_map["Inverter"] = inverter_id
            actions.append(
                AiAction(
                    action=AiActionType.add_component,
                    payload={
                        "id": inverter_id,
                        "name": "Inverter",
                        "type": "inverter",
                        "standard_code": "INV-STD",
                        "x": 400,
                        "y": 100,
                        "layer": "Single-Line Diagram",
                    },
                    version=1,
                ).model_dump()
            )
            battery_id = generate_id("component")
            id_map["Battery"] = battery_id
            actions.append(
                AiAction(
                    action=AiActionType.add_component,
                    payload={
                        "id": battery_id,
                        "name": "Battery",
                        "type": "battery",
                        "standard_code": "BAT-STD",
                        "x": 550,
                        "y": 200,
                        "layer": "Single-Line Diagram",
                    },
                    version=1,
                ).model_dump()
            )

            for i in range(num_panels):
                actions.append(
                    AiAction(
                        action=AiActionType.add_link,
                        payload={
                            "source_id": id_map[f"Panel {i + 1}"],
                            "target_id": inverter_id,
                        },
                        version=1,
                    ).model_dump()
                )
            actions.append(
                AiAction(
                    action=AiActionType.add_link,
                    payload={"source_id": inverter_id, "target_id": battery_id},
                    version=1,
                ).model_dump()
            )
            summary = (
                f"Added {num_panels} panel(s), one inverter and one battery for a {size_kw:g}\xa0kW PV system. "
                "Proposed connecting all panels to the inverter and the inverter to the battery. "
                "Review and approve these actions."
            )
            actions.append(
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": summary},
                    version=1,
                ).model_dump()
            )
            return actions
        elif domain == "HVAC" and size_kw:
            comp_id = generate_id("component")
            evap_id = generate_id("component")
            actions.append(
                AiAction(
                    action=AiActionType.add_component,
                    payload={
                        "id": comp_id,
                        "name": "Compressor",
                        "type": "compressor",
                        "standard_code": "COMP-STD",
                        "x": 200,
                        "y": 100,
                        "layer": "Single-Line Diagram",
                    },
                    version=1,
                ).model_dump()
            )
            actions.append(
                AiAction(
                    action=AiActionType.add_component,
                    payload={
                        "id": evap_id,
                        "name": "Evaporator Coil",
                        "type": "evaporator",
                        "standard_code": "EVA-STD",
                        "x": 350,
                        "y": 200,
                        "layer": "Single-Line Diagram",
                    },
                    version=1,
                ).model_dump()
            )
            actions.append(
                AiAction(
                    action=AiActionType.add_link,
                    payload={"source_id": comp_id, "target_id": evap_id},
                    version=1,
                ).model_dump()
            )
            actions.append(
                AiAction(
                    action=AiActionType.validation,
                    payload={
                        "message": f"Added a compressor and evaporator coil for an HVAC system sized at {size_kw:g}\xa0kW. A connection has been proposed between them.",
                    },
                    version=1,
                ).model_dump()
            )
            return actions
        elif domain == "Water" and size_kw:
            actions.append(
                AiAction(
                    action=AiActionType.add_component,
                    payload={
                        "name": "Water Pump",
                        "type": "pump",
                        "standard_code": "PUMP-STD",
                        "x": 200,
                        "y": 150,
                        "layer": "Single-Line Diagram",
                    },
                    version=1,
                ).model_dump()
            )
            actions.append(
                AiAction(
                    action=AiActionType.validation,
                    payload={
                        "message": f"Added a pump for a water pumping system sized at {size_kw:g}\xa0kW. Approve to place on the canvas.",
                    },
                    version=1,
                ).model_dump()
            )
            return actions

        message = (
            "I'm not sure which domain you're working in.  Please specify whether you're designing a solar, HVAC or water pumping system, and include the desired capacity (e.g., '5\xa0kW solar system')."
        )
        action = AiAction(action=AiActionType.validation, payload={"message": message}, version=1).model_dump()
        return [action]


# instantiate the agent so the registry stores an instance
system_design_agent = register(SystemDesignAgent())

