"""Agent responsible for fetching and parsing component datasheets.

In Phase\xa01 this agent is a stub that demonstrates how a datasheet fetch would be
acknowledged.  In a full implementation it would download a PDF from an external
service (e.g. Octopart) or process a user-uploaded PDF using the existing
file_service parsing pipeline, then insert the resulting structured data into
the component master database.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.schemas.ai import AiAction, AiActionType


class DatasheetFetchAgent(AgentBase):
    """Fetches datasheets and stores parsed data (stub implementation)."""

    name = "datasheet_fetch_agent"
    description = "Fetch component datasheets and store parsed data into the master database."

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        match = re.search(r"(?:datasheet\s+for\s+)?([A-Za-z0-9\-]+)", command)
        part_number = match.group(1) if match else None
        if not part_number:
            return []
        message = (
            f"The datasheet for '{part_number}' has been fetched. "
            "Once parsed, the extracted data (including any variants or options) "
            "will be presented for review.  After approval, the new component or its variants will be added to the library."
        )
        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]


# instantiate the agent so the registry stores an instance
datasheet_fetch_agent = register(DatasheetFetchAgent())
register_spec(name="datasheet_fetch_agent", domain="design", capabilities=["components:create"])

