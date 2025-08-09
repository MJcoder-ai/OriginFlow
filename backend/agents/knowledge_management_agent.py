from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.schemas.ai import AiAction, AiActionType
from backend.services.design_knowledge_service import DesignKnowledgeService
from backend.database.session import SessionMaker
from backend.models.memory import Memory


class KnowledgeManagementAgent(AgentBase):
    """Saves and manages design templates."""

    name = "knowledge_management_agent"
    description = "Saves the current design snapshot as a reusable template."

    async def handle(self, command: str, snapshot: dict | None = None, **kwargs) -> List[Dict[str, Any]]:
        match = re.search(r"named\s+'?([^']+)'?", command, re.IGNORECASE)
        template_name = match.group(1) if match else "Untitled Template"

        if snapshot is None:
            snapshot = {}
        elif hasattr(snapshot, "model_dump"):
            snapshot = snapshot.model_dump()

        async with SessionMaker() as session:
            svc = DesignKnowledgeService(session)
            await svc.save_design_as_template(snapshot, template_name)
            try:
                mem = Memory(
                    tenant_id="tenant_default",
                    project_id=None,
                    kind="template",
                    tags={"name": template_name},
                    trace_id=kwargs.get("trace_id"),
                )
                session.add(mem)
                await session.commit()
            except Exception:
                pass

        message = f"Successfully saved the current design as template: '{template_name}'"
        action = AiAction(
            action=AiActionType.validation,
            payload={"message": message},
            version=1,
        ).model_dump()
        return [action]


knowledge_management_agent = register(KnowledgeManagementAgent())
register_spec(name="knowledge_management_agent", domain="design", capabilities=["design:save"])
