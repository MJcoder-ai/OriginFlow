# backend/agents/layout_agent.py
"""Stub for future layout agent."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register


class LayoutAgent(AgentBase):
    """Organises component positions on the canvas."""

    name = "layout_agent"
    description = "Organises component positions"

    async def handle(self, command: str) -> List[Dict[str, Any]]:  # pragma: no cover - stub
        """Return an empty list until implemented."""

        return []


register(LayoutAgent())
