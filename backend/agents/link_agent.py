# backend/agents/link_agent.py
"""Agent handling link-related commands."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import AsyncOpenAI, OpenAIError
from fastapi import HTTPException

from backend.utils.llm import safe_tool_calls

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.config import settings
from backend.schemas.ai import AiAction, AiActionType
from backend.schemas.link import LinkCreate

client = AsyncOpenAI(api_key=settings.openai_api_key)


class LinkAgent(AgentBase):
    """Adds or removes links using OpenAI function-calling."""

    name = "link_agent"
    description = "Adds or removes links between components or suggests them."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Return validated link actions."""

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_link",
                    "description": "Create a link between components.",
                    "parameters": LinkCreate.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "suggest_link",
                    "description": "Suggest a logical link without committing.",
                    "parameters": LinkCreate.model_json_schema(),
                },
            },
        ]
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model_agents,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                messages=[{"role": "user", "content": command}],
                tools=tools,
                tool_choice="auto",
            )
            tool_calls = safe_tool_calls(response)
        except (OpenAIError, ValueError) as err:
            raise HTTPException(status_code=422, detail=str(err))

        actions: List[Dict[str, Any]] = []
        for call in tool_calls:
            payload = json.loads(call.function.arguments)
            LinkCreate(**payload)
            kind = AiActionType.add_link if call.function.name == "add_link" else AiActionType.suggest_link
            actions.append(
                AiAction(action=kind, payload=payload, version=1).model_dump()
            )
        if not actions:
            raise ValueError("LinkAgent produced no actions")
        return actions


register(LinkAgent())
