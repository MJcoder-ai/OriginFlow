from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.schemas.ai import AiAction, AiActionType
from backend.services.component_db_service import get_component_db_service


class DesignAssemblyAgent(AgentBase):
    """Generates sub-assemblies for components based on dependencies."""

    name = "design_assembly_agent"
    description = (
        "Looks up a component's dependencies and proposes sub-components for detailed layers."
    )

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
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

        if not target:
            msg = f"No component named {name} found."
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": msg},
                    version=1,
                ).model_dump()
            ]

        requires: list[str] = (
            target.dependencies.get("requires", []) if target.dependencies else []
        )

        sub_elements: list[str] = []
        if target.sub_elements:
            for elem in target.sub_elements:
                if isinstance(elem, str):
                    sub_elements.append(elem)
                elif isinstance(elem, dict):
                    n = elem.get("name") or elem.get("part_number") or elem.get("id")
                    if n:
                        sub_elements.append(n)

        if not requires and not sub_elements:
            msg = f"No dependency or sub-element information found for {name}."
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": msg},
                    version=1,
                ).model_dump()
            ]

        layer_affinity: list[str] = target.layer_affinity or []
        target_layer = next(
            (l for l in layer_affinity if l.lower() != "single-line"), "Electrical Detail"
        )

        actions: List[Dict[str, Any]] = []

        def append_add_action(item_name: str) -> None:
            payload = {
                "name": item_name,
                "type": item_name,
                "standard_code": item_name,
                "layer": target_layer,
            }
            actions.append(
                AiAction(
                    action=AiActionType.add_component,
                    payload=payload,
                    version=1,
                ).model_dump()
            )

        for item in requires:
            append_add_action(item)
        for item in sub_elements:
            append_add_action(item)

        summary_parts = []
        if requires:
            summary_parts.append(
                f"{len(requires)} required item{'s' if len(requires) != 1 else ''}"
            )
        if sub_elements:
            summary_parts.append(
                f"{len(sub_elements)} sub-element{'s' if len(sub_elements) != 1 else ''}"
            )
        summary_text = ", ".join(summary_parts) if summary_parts else "no additional items"
        summary = (
            f"Generated sub-assembly for {target.name}: added {summary_text} to the {target_layer} layer."
        )
        actions.append(
            AiAction(
                action=AiActionType.validation,
                payload={"message": summary},
                version=1,
            ).model_dump()
        )
        return actions


design_assembly_agent = register(DesignAssemblyAgent())
register_spec(name="design_assembly_agent", domain="design")

