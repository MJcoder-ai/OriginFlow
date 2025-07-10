# backend/agents/layout_agent.py
"""Stub for future layout agent."""
from __future__ import annotations

from typing import Any, Dict, List
import json

from openai import AsyncOpenAI

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.config import settings
from backend.schemas.ai import AiAction, AiActionType

client = AsyncOpenAI(api_key=settings.openai_api_key)


class LayoutAgent(AgentBase):
    """Organises component positions on the canvas."""

    name = "layout_agent"
    description = "Organises component positions"

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Return position update actions."""

        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["id", "x", "y"],
        }
        response = await client.chat.completions.create(
            model=settings.openai_model_agents,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            messages=[{"role": "user", "content": command}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "set_position",
                    "description": "Move a component to (x,y) on the canvas.",
                    "parameters": schema,
                },
            }],
            tool_choice="auto",
        )
        actions: List[Dict[str, Any]] = []
        for call in response.choices[0].message.tool_calls:
            payload = json.loads(call.function.arguments)
            actions.append(
                AiAction(action=AiActionType.update_position, payload=payload, version=1).model_dump()
            )
        return actions


register(LayoutAgent())
