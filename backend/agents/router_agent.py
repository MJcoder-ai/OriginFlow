# backend/agents/router_agent.py
"""LLM-powered router that selects specialist agents."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import AsyncClient

from backend.agents.base import AgentBase
from backend.agents.registry import get_agent, get_agent_names
from backend.config import settings

client = AsyncClient(api_key=settings.openai_api_key)


class RouterAgent(AgentBase):
    """Classifies commands and dispatches to specialist agents."""

    name = "router_agent"
    description = "Selects the most suitable specialist agent(s) for a command."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Return aggregated actions from relevant specialist agents."""

        agents = get_agent_names()
        response = await client.chat.completions.create(
            model=settings.openai_model_router,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            messages=[{"role": "user", "content": command}],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "route_to_agent",
                        "description": "Pick one or more agents to satisfy the command.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "agent_names": {
                                    "type": "array",
                                    "items": {"type": "string", "enum": agents},
                                    "minItems": 1,
                                }
                            },
                            "required": ["agent_names"],
                        },
                    },
                }
            ],
            tool_choice={"type": "function", "function": {"name": "route_to_agent"}},
        )
        agent_names: List[str] = json.loads(
            response.choices[0].message.tool_calls[0].function.arguments
        )["agent_names"]
        actions: List[Dict[str, Any]] = []
        for name in agent_names:
            specialist = get_agent(name)
            actions.extend(await specialist.handle(command))
        return actions
