# backend/agents/component_agent.py
"""Agent handling component-related commands."""
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
from backend.schemas.component import ComponentCreate

client = AsyncOpenAI(api_key=settings.openai_api_key)


class ComponentAgent(AgentBase):
    """Adds or removes components using OpenAI function-calling."""

    name = "component_agent"
    description = "Adds or removes components."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Return validated component actions."""

        try:
            response = await client.chat.completions.create(
                model=settings.openai_model_agents,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                messages=[{"role": "user", "content": command}],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "add_component",
                            "description": "Add components to the design.",
                            "parameters": ComponentCreate.model_json_schema(),
                        },
                    }
                ],
                tool_choice="auto",
            )
            tool_calls = safe_tool_calls(response)
        except (OpenAIError, ValueError) as err:
            # bubble up as 422 so UI can show "couldn't understand"
            raise HTTPException(status_code=422, detail=str(err))

        actions: List[Dict[str, Any]] = []
        for call in tool_calls:
            if call.function.name == "add_component":
                payload = json.loads(call.function.arguments)
                ComponentCreate(**payload)
                actions.append(
                    AiAction(
                        action=AiActionType.add_component, payload=payload, version=1
                    ).model_dump()
                )
        if not actions:
            raise ValueError("ComponentAgent produced no actions")
        return actions


register(ComponentAgent())
