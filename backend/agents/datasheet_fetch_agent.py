"""Stub agent that acknowledges datasheet fetch requests."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiAction, AiActionType


@register
class DatasheetFetchAgent(AgentBase):
    """Fetch and parse datasheets (placeholder)."""

    name = "datasheet_fetch_agent"
    description = "Fetch component datasheets and store parsed data."

    async def handle(self, command: str) -> List[Dict[str, Any]]:
        match = re.search(r"datasheet\s+for\s+(\S+)", command, re.IGNORECASE)
        part_number = match.group(1) if match else None
        if not part_number:
            return []
        message = (
            f"Datasheet for {part_number} has been fetched and parsed into the component database (stub)."
        )
        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]
