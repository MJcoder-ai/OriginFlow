from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType
from backend.services.component_db_service import get_component_db_service


@register
class DesignAssemblyAgent(AgentBase):
    """Generates sub-assemblies for components based on dependencies."""

    name = "design_assembly_agent"
    description = (
        "Looks up a component's dependencies and proposes sub-components for detailed layers."
    )

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        text = command.lower()
        if "sub" not in text:
            return []
        m = re.search(r"for\s+([\w\- ]+)", text)
        if not m:
            msg = "Please specify a component name to generate its sub-assembly."
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": msg},
                    version=1,
                ).model_dump()
            ]
        name = m.group(1).strip()
        async for svc in get_component_db_service():
            comps = await svc.search()
            break
        target = None
        for c in comps:
            if c.name.lower() == name.lower():
                target = c
                break
        if not target or not target.dependencies or "requires" not in target.dependencies:
            msg = f"No dependency information found for {name}."
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": msg},
                    version=1,
                ).model_dump()
            ]
        actions: List[Dict[str, Any]] = []
        for dep in target.dependencies.get("requires", []):
            actions.append(
                AiAction(
                    action=AiActionType.add_component,
                    payload={
                        "name": f"{dep} for {target.name}",
                        "type": dep,
                        "standard_code": dep.upper(),
                        "x": 100,
                        "y": 100,
                        "layer": "Electrical Detail",
                    },
                    version=1,
                ).model_dump()
            )
        actions.append(
            AiAction(
                action=AiActionType.validation,
                payload={"message": f"Generated {len(actions)} sub-components for {target.name}."},
                version=1,
            ).model_dump()
        )
        return actions


design_assembly_agent = register(DesignAssemblyAgent())
