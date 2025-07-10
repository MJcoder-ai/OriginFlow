# backend/agents/layout_agent.py
"""Stub for future layout agent."""
from __future__ import annotations

from typing import Any, Dict, List
import json

from openai import AsyncOpenAI, OpenAIError
from fastapi import HTTPException

from backend.utils.llm import safe_tool_calls
from backend.schemas.ai import AiAction, AiActionType, PositionPayload

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.config import settings


client = AsyncOpenAI(api_key=settings.openai_api_key)


class LayoutAgent(AgentBase):
    """Organises component positions on the canvas."""

    name = "layout_agent"
    description = "Organises component positions"

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Return position update actions."""

        schema = PositionPayload.model_json_schema()
        try:
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
            tool_calls = safe_tool_calls(response)
        except (OpenAIError, ValueError) as err:
            raise HTTPException(status_code=422, detail=str(err))
        actions: List[Dict[str, Any]] = []
        for call in tool_calls:
            payload = PositionPayload.model_validate_json(call.function.arguments).model_dump()
            actions.append(
                AiAction(action=AiActionType.update_position, payload=payload, version=1).model_dump()
            )
        return actions


register(LayoutAgent())
