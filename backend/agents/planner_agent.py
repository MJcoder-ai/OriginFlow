"""Simple planner that emits canonical task IDs."""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.services import odl_graph_service


class PlannerAgent:
    """Interprets user commands and produces a task list."""

    def __init__(self) -> None:
        self.odl_graph_service = odl_graph_service

    async def plan(
        self, session_id: str, command: str, *, requirements: Optional[Dict] = None
    ) -> List[Dict]:
        """Dynamically generate a task list based on session state and intent."""
        cmd = command.lower().strip()
        if not cmd.startswith("design"):
            return []

        graph = await self.odl_graph_service.get_graph(session_id)
        has_panel = any(
            n for n, data in graph.nodes(data=True) if data.get("type") == "panel"
        )
        has_inverter = any(
            n for n, data in graph.nodes(data=True) if data.get("type") == "inverter"
        )

        tasks: List[Dict[str, str]] = []
        if not requirements or not all(
            k in requirements for k in ["target_power", "roof_area", "budget"]
        ):
            tasks.append({"id": "gather_requirements", "status": "pending"})
        if not (has_panel and has_inverter):
            tasks.append({"id": "generate_design", "status": "pending"})
        tasks.append({"id": "refine_validate", "status": "pending"})
        return tasks
