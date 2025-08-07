import json
from typing import Any, Dict, List

from openai import AsyncOpenAI

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.config import settings
from backend.schemas.ai import AiAction, AiActionType
from backend.services.ai_clients import get_openai_client


class AuditorAgent(AgentBase):
    """Validates a design against IEC/UL rules."""

    name = "auditor_agent"
    description = "Validates designs for compliance"

    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "validation",
                    "description": "Return validation results as text.",
                    "parameters": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    },
                },
            }
        ]
        response = await self.client.chat.completions.create(
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
                AiAction(action=AiActionType.validation, payload=payload, version=1).model_dump()
            )
        return actions


auditor_agent = register(AuditorAgent(get_openai_client()))
register_spec(name="auditor_agent", domain="design", capabilities=["design:validate"])
