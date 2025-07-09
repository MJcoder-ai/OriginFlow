# backend/agents/base.py
"""Base class for AI agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AgentBase(ABC):
    """Common interface for all agents."""

    name: str = ""
    description: str = ""

    @abstractmethod
    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Process ``command`` and return a list of action dictionaries."""

        raise NotImplementedError
