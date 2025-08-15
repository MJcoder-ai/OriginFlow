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

    async def execute(self, session_id: str, tid: str, **kwargs) -> Any:
        """Override to perform work for a given task."""
        raise NotImplementedError

    async def safe_execute(self, session_id: str, tid: str, **kwargs) -> Dict[str, Any]:
        """
        Wrap ``execute`` to catch errors and return a fallback ADPF envelope.

        Agents should call this method from the orchestrator to ensure that
        unexpected exceptions are handled gracefully.  If ``execute`` raises
        an :class:`OriginFlowError`, the error message is returned to the user
        with status ``blocked``.  All other exceptions produce a generic error
        message and log the exception.
        """
        from backend.utils.adpf import wrap_response  # local import to avoid cycles
        from backend.utils.errors import OriginFlowError

        try:
            return await self.execute(session_id, tid, **kwargs)
        except OriginFlowError as e:
            return wrap_response(
                thought=f"Agent '{self.name}' encountered a recoverable error.",
                card={
                    "title": f"{self.name.replace('_', ' ').title()}",
                    "body": str(e),
                    "warnings": [
                        "This task has been blocked due to a conflict or invalid input."
                    ],
                },
                patch=None,
                status="blocked",
            )
        except Exception as e:  # pragma: no cover - defensive
            import logging

            logger = logging.getLogger(f"originflow.{self.name}")
            logger.exception("Unhandled exception in agent '%s'", self.name)
            return wrap_response(
                thought=f"Agent '{self.name}' failed with an unexpected error.",
                card={
                    "title": f"{self.name.replace('_', ' ').title()}",
                    "body": "An unexpected error occurred. Please try again or contact support.",
                },
                patch=None,
                status="blocked",
            )
