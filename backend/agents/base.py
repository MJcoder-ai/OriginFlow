# backend/agents/base.py
"""Base class for AI agents with retry and discovery support.

This interface underpins OriginFlow's agent system and now includes
optional metadata used by the plug‑in architecture.  The additional
fields enable runtime discovery and UI hints while remaining backward
compatible with existing agents.
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Dict, List

from backend.utils.retry_manager import retry_manager
from backend.utils.schema_enforcer import validate_envelope


class AgentBase(ABC):
    """Common interface for all agents.

    Agents may optionally declare metadata for discovery:

    - ``domain``: High-level domain this agent operates in (e.g. ``pv``).
    - ``risk_class``: Risk classification used by auto‑approval policies.
    - ``capabilities``: List of capability keywords.
    - ``examples``: Sample commands that the agent can handle.

    Existing agents can ignore these attributes and continue to
    implement ``handle`` and ``execute`` as before.
    """

    name: str = ""
    description: str = ""
    domain: str = ""
    risk_class: str = "low"
    capabilities: List[str] = []
    examples: List[str] = []

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        """Return a list of AiAction dicts.

        Accepts optional keyword arguments such as ``snapshot`` or ``context``.
        Concrete agents may ignore unknown keys.
        """

        raise NotImplementedError(
            "Agent must implement handle(command, **kwargs))"
        )

    def can_handle(self, command: str) -> bool:
        """Return ``True`` if this agent can handle ``command``.

        The default implementation matches the agent's ``name`` or
        ``domain`` within the command string.  Agents with more
        sophisticated routing logic should override this method.
        """

        cmd = command.lower()
        return bool(
            (self.domain and self.domain.lower() in cmd)
            or (self.name and self.name.lower() in cmd)
        )

    async def execute(self, session_id: str, tid: str, **kwargs) -> Any:
        """Override to perform work for a given task."""
        raise NotImplementedError

    async def safe_execute(
        self, session_id: str, tid: str, **kwargs
    ) -> Dict[str, Any]:
        """Execute the task with error handling and retry registration."""
        from backend.utils.adpf import (
            wrap_response,
        )  # local import to avoid cycles
        from backend.utils.errors import OriginFlowError

        try:
            result = await self.execute(session_id, tid, **kwargs)
            if isinstance(result, dict):
                try:
                    validate_envelope(result)
                except Exception as exc:
                    response = wrap_response(
                        thought=(
                            "Invalid envelope returned by agent "
                            f"'{self.name}' for task '{tid}'"
                        ),
                        card={
                            "title": f"{self.name.replace('_', ' ').title()}",
                            "body": str(exc),
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
                status = result.get("status") or result.get(
                    "output", {}
                ).get("status")
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
                thought=(
                    f"Agent '{self.name}' encountered a recoverable error."
                ),
                card={
                    "title": f"{self.name.replace('_', ' ').title()}",
                    "body": str(exc),
                    "warnings": [
                        "This task has been blocked due to a conflict or "
                        "invalid input.",
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
                thought=(
                    f"Agent '{self.name}' failed with an unexpected error."
                ),
                card={
                    "title": f"{self.name.replace('_', ' ').title()}",
                    "body": (
                        "An unexpected error occurred. Please try again or "
                        "contact support."
                    ),
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
