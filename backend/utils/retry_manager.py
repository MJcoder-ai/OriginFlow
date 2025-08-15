"""Utilities for tracking and retrying blocked agent tasks."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


class RetryManager:
    """Simple in-memory tracker for blocked tasks.

    Tasks are grouped per session.  Each task record stores the agent name,
    task identifier and original context so that it can be retried later.
    """

    def __init__(self) -> None:
        self._blocked: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def register_blocked_task(
        self,
        *,
        session_id: str,
        agent_name: str,
        task_id: str,
        context: Dict[str, Any] | None = None,
    ) -> None:
        """Record a blocked task for later retry."""

        self._blocked[session_id].append(
            {
                "agent_name": agent_name,
                "task_id": task_id,
                "context": context or {},
            }
        )

    async def resolve_blocked_tasks(self, session_id: str) -> List[Dict[str, Any]]:
        """Attempt to resolve all blocked tasks for ``session_id``.

        Returns a list of results from each task execution.  Tasks that return a
        non-blocked status are removed from the queue.  Remaining blocked tasks
        stay queued for future attempts.
        """

        tasks = self._blocked.get(session_id, [])
        if not tasks:
            return []

        remaining: List[Dict[str, Any]] = []
        results: List[Dict[str, Any]] = []
        from backend.agents.registry import get_agent  # local import to avoid cycles

        for item in tasks:
            agent = get_agent(item["agent_name"])
            result = await agent.safe_execute(
                session_id, item["task_id"], **item.get("context", {})
            )
            results.append(result)
            if isinstance(result, dict):
                status = result.get("status") or result.get("output", {}).get("status")
                if status == "blocked":
                    remaining.append(item)

        if remaining:
            self._blocked[session_id] = remaining
        else:
            self._blocked.pop(session_id, None)

        return results

    def get_blocked_tasks(self, session_id: str) -> List[Dict[str, Any]]:
        """Return current blocked tasks for ``session_id``."""

        return list(self._blocked.get(session_id, []))


retry_manager = RetryManager()

