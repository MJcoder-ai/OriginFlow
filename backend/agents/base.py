# backend/agents/base.py
"""Base class for AI agents with retry support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from backend.utils.retry_manager import retry_manager


class AgentBase(ABC):
    """Common interface for all agents."""

    name: str = ""
    description: str = ""

    @abstractmethod
    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """Return a list of AiAction dicts.

        Accepts optional keyword arguments such as ``snapshot`` or ``context``.
        Concrete agents may ignore unknown keys.
        """

        raise NotImplementedError("Agent must implement handle(command, **kwargs))")

    async def execute(self, session_id: str, tid: str, **kwargs) -> Any:
        """Override to perform work for a given task."""
        raise NotImplementedError

    async def safe_execute(self, session_id: str, tid: str, **kwargs) -> Dict[str, Any]:
        """Execute the task with error handling and retry registration."""
        from backend.utils.adpf import wrap_response  # local import to avoid cycles
        from backend.utils.errors import OriginFlowError

        try:
            result = await self.execute(session_id, tid, **kwargs)
            if isinstance(result, dict):
                status = result.get("status") or result.get("output", {}).get("status")
                if status == "blocked":
                    retry_manager.register_blocked_task(
                        session_id=session_id,
                        agent_name=self.name,
                        task_id=tid,
                        context=kwargs,
                    )
            return result
        except OriginFlowError as exc:
            response = wrap_response(
                thought=f"Agent '{self.name}' encountered a recoverable error.",
                card={
                    "title": f"{self.name.replace('_', ' ').title()}",
                    "body": str(exc),
                    "warnings": [
                        "This task has been blocked due to a conflict or invalid input.",
                    ],
                },
                patch=None,
                status="blocked",
            )
            retry_manager.register_blocked_task(
                session_id=session_id,
                agent_name=self.name,
                task_id=tid,
                context=kwargs,
            )
            return response
        except Exception:  # pragma: no cover - defensive
            import logging

            logger = logging.getLogger(f"originflow.{self.name}")
            logger.exception("Unhandled exception in agent '%s'", self.name)
            response = wrap_response(
                thought=f"Agent '{self.name}' failed with an unexpected error.",
                card={
                    "title": f"{self.name.replace('_', ' ').title()}",
                    "body": "An unexpected error occurred. Please try again or contact support.",
                },
                patch=None,
                status="blocked",
            )
            retry_manager.register_blocked_task(
                session_id=session_id,
                agent_name=self.name,
                task_id=tid,
                context=kwargs,
            )
            return response

