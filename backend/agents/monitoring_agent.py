"""
MonitoringAgent implements automatic placement of monitoring devices into an ODL design.

This agent is triggered by the ``generate_monitoring`` task and adds one or more
monitoring nodes to the system.  Monitoring devices are attached to inverters,
battery modules or other key components via communication links.  The agent
produces a design card summarising the sensors added and a graph patch to
update the design.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.services import odl_graph_service
from backend.services.placeholder_components import get_placeholder_service
from backend.schemas.odl import ODLNode, ODLEdge, GraphPatch
from backend.utils.adpf import wrap_response


class MonitoringAgent(AgentBase):
    """Agent responsible for adding system monitoring devices."""

    name = "monitoring_agent"
    domain = "monitoring"

    async def execute(self, session_id: str, tid: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Handle ``generate_monitoring`` tasks by adding placeholder monitoring devices.

        The method inspects the current design graph associated with ``session_id``
        and identifies components that should be instrumented, such as inverters
        and battery modules.  For each target component, it creates a generic
        monitoring node and connects it with a communication link.  If no suitable
        targets exist, the agent attaches a monitoring device to the first node in
        the graph.  The result is an ADPF envelope containing a card and patch.
        """
        task = tid.lower().strip()
        thought = "Placing monitoring devices to enable system telemetry."
        if task != "generate_monitoring":
            return wrap_response(
                thought=f"Received unsupported task '{tid}' in MonitoringAgent.",
                card={
                    "title": "Monitoring design",
                    "body": f"Task '{tid}' is not handled by MonitoringAgent.",
                },
                patch=None,
                status="pending",
            )

        graph = await odl_graph_service.get_graph(session_id)
        if graph is None:
            return wrap_response(
                thought="Unable to retrieve design graph for monitoring placement.",
                card={
                    "title": "Monitoring design",
                    "body": "Session not found. Please create a design before adding monitoring.",
                },
                patch=None,
                status="blocked",
            )

        placeholder_service = get_placeholder_service()
        targets: List[str] = [
            n for n, d in graph.nodes(data=True)
            if d.get("type") in {"inverter", "battery", "generic_battery"}
        ]
        if not targets and graph.nodes:
            targets = [next(iter(graph.nodes))]

        added_nodes: List[ODLNode] = []
        added_edges: List[ODLEdge] = []

        for idx, target_id in enumerate(targets, start=1):
            node_id = f"monitor_{target_id}_{idx}"
            monitor_dict = placeholder_service.create_placeholder_node(
                node_id=node_id,
                component_type="generic_monitoring",
            )
            monitor_node = ODLNode(**monitor_dict)
            added_nodes.append(monitor_node)
            edge = ODLEdge(
                source=monitor_node.id,
                target=target_id,
                data={"type": "communication"},
                connection_type="communication",
            )
            added_edges.append(edge)

        if not added_nodes:
            return wrap_response(
                thought="No suitable targets found for monitoring placement.",
                card={
                    "title": "Monitoring design",
                    "body": "No components require monitoring in the current design.",
                },
                patch=None,
                status="complete",
            )

        patch = GraphPatch(add_nodes=added_nodes, add_edges=added_edges)
        card = {
            "title": "Monitoring design",
            "body": f"Added {len(added_nodes)} monitoring device(s) to the design.",
            "specs": {
                "device_type": "generic_monitoring",
                "instrumented_components": targets,
            },
            "recommended_actions": [
                "Verify data logging and communication settings.",
                "Proceed to validate cross-layer connections and compliance.",
            ],
        }
        return wrap_response(
            thought=thought,
            card=card,
            patch=patch.model_dump(),
            status="complete",
            warnings=None,
        )
