from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import AsyncOpenAI

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.config import settings
from backend.schemas.ai import AiAction, AiActionType

client = AsyncOpenAI(api_key=settings.openai_api_key)


class BomAgent(AgentBase):
    """Generates a bill of materials report."""

    name = "bom_agent"
    description = "Produce bill of materials for the design"

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "report",
                    "description": "Return bill of materials entries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["items"],
                    },
                },
            }
        ]
        response = await client.chat.completions.create(
            model=settings.openai_model_agents,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            messages=[{"role": "user", "content": command}],
            tools=tools,
            tool_choice="auto",
        )
        actions: List[Dict[str, Any]] = []
        for call in response.choices[0].message.tool_calls:
            payload = json.loads(call.function.arguments)
            actions.append(
                AiAction(action=AiActionType.report, payload=payload, version=1).model_dump()
            )
        return actions


register(BomAgent())
