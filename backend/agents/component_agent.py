# backend/agents/component_agent.py
"""Agent handling component-related commands."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import AsyncOpenAI, OpenAIError
from fastapi import HTTPException
from pydantic import BaseModel, Field

from backend.utils.llm import safe_tool_calls

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.config import settings
from backend.schemas.ai import AiAction, AiActionType
from backend.schemas.component import ComponentCreate
from backend.services.component_service import find_component_by_name
from backend.services.component_db_service import get_component_db_service
from backend.services.ai_clients import get_openai_client

# schema for the remove_component tool
class RemoveComponentPayload(BaseModel):
    """Payload identifying a component to remove."""

    name: str = Field(..., description="The name of the component to remove.")


class ComponentAgent(AgentBase):
    """Adds or removes components using OpenAI function-calling."""

    name = "component_agent"
    description = "Adds or removes components."

    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """Return validated component actions."""
        try:
            response = await self.client.chat.completions.create(
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
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "remove_component",
                            "description": "Remove a component from the design by its name.",
                            "parameters": RemoveComponentPayload.model_json_schema(),
                        },
                    },
                ],
                tool_choice="auto",
            )
            tool_calls = safe_tool_calls(response)
        except (OpenAIError, ValueError) as err:
            raise HTTPException(status_code=422, detail=str(err))

        actions: List[Dict[str, Any]] = []
        for call in tool_calls:
            payload = json.loads(call.function.arguments)
            if call.function.name == "add_component":
                ComponentCreate(**payload)
                enriched = dict(payload)
                try:
                    category = None
                    name_lower = enriched.get("name", "").lower()
                    type_lower = enriched.get("type", "").lower()
                    if "inverter" in name_lower or "inverter" in type_lower:
                        category = "inverter"
                    elif "panel" in name_lower or "panel" in type_lower or "solar" in name_lower:
                        category = "panel"
                    elif "battery" in name_lower or "battery" in type_lower:
                        category = "battery"
                    if category:
                        async for svc in get_component_db_service():
                            comp_service = svc
                            break
                        comps = await comp_service.search(category=category)
                        if comps:
                            comps_sorted = sorted(
                                comps,
                                key=lambda c: c.price if c.price is not None else float("inf"),
                            )
                            chosen = comps_sorted[0]
                            enriched["name"] = chosen.name
                            enriched["type"] = chosen.category
                            enriched["standard_code"] = chosen.part_number
                except Exception:
                    # Fall back to original payload if lookup fails
                    enriched = dict(payload)
                actions.append(
                    AiAction(
                        action=AiActionType.add_component,
                        payload=enriched,
                        version=1,
                    ).model_dump()
                )
            elif call.function.name == "remove_component":
                payload = (
                    RemoveComponentPayload.model_validate_json(
                        call.function.arguments
                    ).model_dump()
                )
                comp = await find_component_by_name(payload["name"])
                if not comp:
                    raise HTTPException(404, f'Component "{payload["name"]}" not found')
                actions.append(
                    AiAction(
                        action=AiActionType.remove_component,
                        payload={"id": comp.id, "name": comp.name},
                        version=1,
                    ).model_dump()
                )
        if not actions:
            raise ValueError("ComponentAgent produced no actions")
        return actions


component_agent = register(ComponentAgent(get_openai_client()))
register_spec(
    name="component_agent",
    domain="design",
    risk_class="medium",
    capabilities=[
        "components:read",
        "components:create",
        "components:update",
        "components:delete",
    ],
)
