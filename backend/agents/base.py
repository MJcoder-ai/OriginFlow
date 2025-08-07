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
    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """Return a list of AiAction dicts.

        Accepts optional keyword arguments such as ``snapshot`` or
        ``context``. Concrete agents may ignore unknown keys.
        """

        raise NotImplementedError("Agent must implement handle(command, **kwargs))")
