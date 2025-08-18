# backend/agents/component_agent.py
"""Agent handling component-related commands."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, OpenAIError
from fastapi import HTTPException
from pydantic import BaseModel, Field

from backend.utils.llm import safe_tool_calls

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.config import settings
from backend.schemas.ai import AiAction, AiActionType
from backend.schemas.component import ComponentCreate
from backend.schemas.analysis import DesignSnapshot
from backend.services.ai.state_action_resolver import StateAwareActionResolver
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

    async def _lookup_component(
        self, command: str, snapshot: Optional[DesignSnapshot] = None
    ) -> List[Dict[str, Any]] | None:
        """Attempt a direct database lookup before invoking the LLM."""
        async for svc in get_component_db_service():
            comp_service = svc
            break

        tokens = re.findall(r"[A-Za-z0-9_.-]+", command)
        for tok in tokens:
            comp = await comp_service.get_by_part_number(tok)
            if comp:
                payload = {
                    "name": comp.get("name"),
                    "type": comp.get("category"),
                    "standard_code": comp.get("part_number"),
                    "_resolver": {"confidence": 1.0, "rationale": "matched_part_number"},
                }
                return [
                    AiAction(action=AiActionType.add_component, payload=payload, version=1).model_dump(),
                    AiAction(
                        action=AiActionType.validation,
                        payload={"message": f"Using library component {comp.get('part_number')} from the datasheet"},
                        version=1,
                    ).model_dump(),
                ]

        resolver = StateAwareActionResolver()
        decision = resolver.resolve_add_component(command, snapshot)
        category = decision.component_class
        if not category:
            return None

        comps = await comp_service.search(category=category)
        if not comps:
            payload = {
                "name": f"generic_{category}",
                "type": category,
                "standard_code": None,
                "_resolver": {"confidence": decision.confidence, "rationale": decision.rationale},
            }
            return [
                AiAction(action=AiActionType.add_component, payload=payload, version=1).model_dump(),
                AiAction(
                    action=AiActionType.validation,
                    payload={
                        "message": (
                            f"No {category} in the library; using a generic placeholder. "
                            f"Please upload a {category} datasheet for more accurate results."
                        )
                    },
                    version=1,
                ).model_dump(),
            ]

        comps_sorted = sorted(
            comps, key=lambda c: c.get("price", float("inf"))
        )
        chosen = comps_sorted[0]
        payload = {
            "name": chosen.get("name"),
            "type": chosen.get("category"),
            "standard_code": chosen.get("part_number"),
            "_resolver": {"confidence": decision.confidence, "rationale": decision.rationale},
        }
        message = f"ComponentAgent found {len(comps)} {category}(s); selecting the cheapest."
        return [
            AiAction(action=AiActionType.add_component, payload=payload, version=1).model_dump(),
            AiAction(
                action=AiActionType.validation,
                payload={"message": message},
                version=1,
            ).model_dump(),
        ]

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """Return validated component actions."""

        snapshot: Optional[DesignSnapshot] = kwargs.get("snapshot")
        db_actions = await self._lookup_component(command, snapshot)
        if db_actions is not None:
            return db_actions

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
                validation_msg = None
                try:
                    async for svc in get_component_db_service():
                        comp_service = svc
                        break
                    name_lower = enriched.get("name", "").lower()
                    type_lower = enriched.get("type", "").lower()
                    code = (
                        enriched.get("standard_code") or enriched.get("part_number")
                    )
                    if code:
                        comp = await comp_service.get_by_part_number(code)
                        if comp:
                            enriched["name"] = comp.get("name")
                            enriched["type"] = comp.get("category")
                            enriched["standard_code"] = comp.get("part_number")
                            validation_msg = (
                                f"Using library component {comp.get('part_number')} from the datasheet"
                            )
                    if validation_msg is None:
                        resolver = StateAwareActionResolver()
                        decision = resolver.resolve_add_component(command, snapshot)
                        category = decision.component_class
                        if category:
                            comps = await comp_service.search(category=category)
                            if comps:
                                comps_sorted = sorted(
                                    comps,
                                    key=lambda c: c.get("price", float("inf")),
                                )
                                chosen = comps_sorted[0]
                                enriched["name"] = chosen.get("name")
                                enriched["type"] = chosen.get("category")
                                enriched["standard_code"] = chosen.get("part_number")
                                validation_msg = (
                                    f"ComponentAgent found {len(comps)} {category}(s); selecting the cheapest."
                                )
                            else:
                                enriched["name"] = f"generic_{category}"
                                enriched["type"] = category
                                enriched["standard_code"] = None
                                validation_msg = (
                                    f"No {category} in the library; using a generic placeholder. "
                                    f"Please upload a {category} datasheet for more accurate results."
                                )
                        enriched["_resolver"] = {
                            "confidence": decision.confidence,
                            "rationale": decision.rationale,
                        }
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Component enrichment failed: {e}")
                    enriched = dict(payload)
                actions.append(
                    AiAction(
                        action=AiActionType.add_component,
                        payload=enriched,
                        version=1,
                    ).model_dump()
                )
                if validation_msg:
                    actions.append(
                        AiAction(
                            action=AiActionType.validation,
                            payload={"message": validation_msg},
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
