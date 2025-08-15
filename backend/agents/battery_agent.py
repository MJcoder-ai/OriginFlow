"""
BatteryAgent implements automatic sizing and integration of battery storage into an ODL design.

This agent is triggered by the ``generate_battery`` task produced by the
PlannerAgent.  It inspects the current design graph to determine where battery
storage is needed, creates placeholder battery nodes and connects them to
existing inverters or the system root.  The agent returns an ADPF-compliant
envelope with a design card summarising the additions and a graph patch
containing the new nodes and edges.

Battery sizing is performed heuristically: if no load or backup requirements
are specified in the requirements, a single 10 kWh module is assumed.  Future
versions may integrate with more sophisticated sizing algorithms and battery
catalogues.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.services import odl_graph_service
from backend.services.placeholder_components import get_placeholder_service
from backend.schemas.odl import ODLNode, ODLEdge, GraphPatch
from backend.utils.adpf import wrap_response


class BatteryAgent(AgentBase):
    """Agent responsible for designing battery storage systems."""

    name = "battery_agent"
    domain = "battery"

    async def execute(self, session_id: str, tid: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Handle ``generate_battery`` tasks by adding placeholder battery modules.

        The method inspects the ODL graph associated with ``session_id`` to
        locate inverters or other nodes that require energy storage.  For each
        inverter found, it creates a single placeholder battery node of type
        ``generic_battery`` using the placeholder component service and connects
        it to the inverter with an electrical link.  If no inverters exist,
        a single battery module is attached to the system root.  The method
        returns a design card and patch wrapped in the ADPF envelope.

        Args:
            session_id: Unique identifier of the ODL session.
            tid: Task identifier; must be ``generate_battery``.
            **kwargs: Additional arguments (ignored).

        Returns:
            A dictionary conforming to the ADPF envelope.
        """
        task = tid.lower().strip()
        thought = "Sizing and placing battery modules in the design."
        if task != "generate_battery":
            return wrap_response(
                thought=f"Received unsupported task '{tid}' in BatteryAgent.",
                card={
                    "title": "Battery design",
                    "body": f"Task '{tid}' is not handled by BatteryAgent.",
                },
                patch=None,
                status="pending",
            )

        graph = await odl_graph_service.get_graph(session_id)
        if graph is None:
            return wrap_response(
                thought="Unable to retrieve design graph for battery sizing.",
                card={
                    "title": "Battery design",
                    "body": "Session not found. Please create a design before adding batteries.",
                },
                patch=None,
                status="blocked",
            )

        placeholder_service = get_placeholder_service()

        inverters: List[str] = [
            n for n, d in graph.nodes(data=True) if d.get("type") == "inverter"
        ]

        added_nodes: List[ODLNode] = []
        added_edges: List[ODLEdge] = []

        targets: List[str] = inverters
        if not targets and graph.nodes:
            targets = [next(iter(graph.nodes))]

        for idx, target_id in enumerate(targets, start=1):
            node_id = f"battery_{target_id}_{idx}"
            battery_dict = placeholder_service.create_placeholder_node(
                node_id=node_id,
                component_type="generic_battery",
            )
            battery_node = ODLNode(**battery_dict)
            added_nodes.append(battery_node)
            edge = ODLEdge(
                source=battery_node.id,
                target=target_id,
                data={"type": "electrical"},
                connection_type="electrical",
            )
            added_edges.append(edge)

        if not added_nodes:
            return wrap_response(
                thought="No suitable targets found for battery placement.",
                card={
                    "title": "Battery design",
                    "body": "No components require battery storage in the current design.",
                },
                patch=None,
                status="complete",
            )

        patch = GraphPatch(add_nodes=added_nodes, add_edges=added_edges)
        card = {
            "title": "Battery design",
            "body": f"Added {len(added_nodes)} battery module(s) to the design.",
            "specs": {
                "module_type": "generic_battery",
                "connection_targets": targets,
            },
            "recommended_actions": [
                "Review battery capacity requirements and adjust module sizing if needed.",
                "Proceed to generate the monitoring system to track battery performance.",
            ],
        }
        return wrap_response(
            thought=thought,
            card=card,
            patch=patch.model_dump(),
            status="complete",
            warnings=None,
        )
