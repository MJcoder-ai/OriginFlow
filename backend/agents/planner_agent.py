"""Simple planner that emits canonical task IDs."""
from __future__ import annotations

from typing import Dict, List


class PlannerAgent:
    """Interprets user commands and produces a task list."""

    async def plan(self, session_id: str, command: str) -> List[Dict]:
        """Produce a sequence of high-level tasks for a given command."""
        cmd = command.lower().strip()
        if cmd.startswith("design"):
            return [
                {
                    "id": "gather_requirements",
                    "title": "Gather requirements",
                    "status": "pending",
                },
                {
                    "id": "generate_design",
                    "title": "Generate design",
                    "status": "pending",
                },
                {
                    "id": "refine_validate",
                    "title": "Refine/Validate",
                    "status": "pending",
                },
            ]
        return []
