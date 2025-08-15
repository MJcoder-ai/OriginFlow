from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import AgentBase
from backend.services import odl_graph_service
from backend.utils.adpf import wrap_response


class NetworkAgent(AgentBase):
    """Agent responsible for network topology design."""

    name = "network_agent"
    domain = "network"

    async def execute(self, session_id: str, tid: str, **kwargs: Any) -> Dict[str, Any]:
        """Handle ``generate_network`` tasks by producing a placeholder response."""
        task = tid.lower().strip()
        thought = "Designing network topology and communication links."
        if task != "generate_network":
            return wrap_response(
                thought=f"Unsupported network task '{tid}'.",
                card={
                    "title": "Network design",
                    "body": f"Task '{tid}' is not handled by NetworkAgent.",
                },
                patch=None,
                status="pending",
            )

        graph = await odl_graph_service.get_graph(session_id)
        if graph is None:
            return wrap_response(
                thought="Unable to retrieve design graph for network generation.",
                card={"title": "Network design", "body": "Session not found."},
                patch=None,
                status="blocked",
            )

        card = {
            "title": "Network design",
            "body": "Network design logic is not yet implemented.",
        }
        return wrap_response(
            thought=thought,
            card=card,
            patch=None,
            status="complete",
            warnings=None,
        )
