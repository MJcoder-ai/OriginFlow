from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import AgentBase
from backend.services import odl_graph_service
from backend.utils.adpf import wrap_response


class SitePlanningAgent(AgentBase):
    """Agent responsible for site layout and planning."""

    name = "site_planning_agent"
    domain = "site"

    async def execute(self, session_id: str, tid: str, **kwargs: Any) -> Dict[str, Any]:
        """Handle ``generate_site`` tasks with a placeholder response."""
        task = tid.lower().strip()
        thought = "Evaluating site layout for component placement."
        if task != "generate_site":
            return wrap_response(
                thought=f"Unsupported site planning task '{tid}'.",
                card={
                    "title": "Site planning",
                    "body": f"Task '{tid}' is not handled by SitePlanningAgent.",
                },
                patch=None,
                status="pending",
            )

        graph = await odl_graph_service.get_graph(session_id)
        if graph is None:
            return wrap_response(
                thought="Unable to retrieve design graph for site planning.",
                card={"title": "Site planning", "body": "Session not found."},
                patch=None,
                status="blocked",
            )

        card = {
            "title": "Site planning",
            "body": "Site planning logic is not yet implemented.",
        }
        return wrap_response(
            thought=thought,
            card=card,
            patch=None,
            status="complete",
            warnings=None,
        )
