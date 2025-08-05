# backend/agents/router_agent.py
"""LLM-powered router that selects specialist agents."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import AsyncOpenAI
from fastapi import HTTPException

from backend.agents.base import AgentBase
from backend.agents.registry import get_agent, get_agent_names
from backend.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


class RouterAgent(AgentBase):
    """Classifies commands and dispatches to specialist agents."""

    name = "router_agent"
    description = "Selects the most suitable specialist agent(s) for a command."

    async def handle(self, command: str, snapshot: dict | None = None) -> List[Dict[str, Any]]:
        """Return aggregated actions from relevant specialist agents."""

        agents = get_agent_names()

        system_prompt = (
            "You are a router that maps user commands to agent names.\n"
            "Available agents: " + ", ".join(agents) + ".\n"
            "Return exactly one JSON tool call."
        )
        examples = [
            {"user": "add inverter", "agent": "component_agent"},
            {"user": "delete battery", "agent": "component_agent"},
            {"user": "connect panel to inverter", "agent": "link_agent"},
            {"user": "organise the layout", "agent": "layout_agent"},
            {"user": "validate my design", "agent": "auditor_agent"},
            {"user": "what is the bill of materials", "agent": "bom_agent"},
            {"user": "design a 5 kW solar system", "agent": "system_design_agent"},
            {"user": "find panels", "agent": "inventory_agent"},
            {"user": "datasheet for ABC123", "agent": "datasheet_fetch_agent"},
            {"user": "generate sub assembly for inverter", "agent": "design_assembly_agent"},
            {"user": "size wiring for 5 kW over 20 m", "agent": "wiring_agent"},
            {"user": "estimate performance", "agent": "performance_agent"},
            {"user": "validate connections", "agent": "cross_layer_validation_agent"},
            {"user": "estimate system performance", "agent": "performance_agent"},
            {"user": "estimate cost of a 5 kW solar system", "agent": "financial_agent"},
            {"user": "how much will a 3 ton hvac cost", "agent": "financial_agent"},
            {"user": "save this design as a template", "agent": "knowledge_management_agent"},
        ]
        msgs = [{"role": "system", "content": system_prompt}]
        for ex in examples:
            msgs += [
                {"role": "user", "content": ex["user"]},
                {"role": "assistant", "content": f'{{"agent_names":["{ex["agent"]}"]}}'},
            ]
        msgs += [{"role": "user", "content": command}]

        response = await client.chat.completions.create(
            model=settings.openai_model_router,
            temperature=0,
            max_tokens=20,
            messages=msgs,
            tools=[{
                "type": "function",
                "function": {
                    "name": "route_to_agent",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_names": {"type": "array", "items": {"type": "string", "enum": agents}},
                        },
                        "required": ["agent_names"],
                    },
                }}],
            tool_choice={"type": "function", "function": {"name": "route_to_agent"}},
        )
        try:
            selected = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["agent_names"]
        except Exception:
            raise HTTPException(422, "Router could not classify the command")

        actions: List[Dict[str, Any]] = []
        for name in selected:
            if name == "knowledge_management_agent":
                actions += await get_agent(name).handle(command, snapshot)
            else:
                actions += await get_agent(name).handle(command)
        return actions

