"""Structural agent for generating mounting hardware."""
from __future__ import annotations

from typing import Dict, List

from backend.services.odl_graph_service import get_graph
from backend.schemas.odl import ODLNode, ODLEdge, GraphPatch


class StructuralAgent:
    """
    Agent responsible for structural sizing. For each panel in the graph, this
    agent adds a mount node with a placeholder load rating and a `mounted_on`
    edge connecting the mount to the panel. Future versions should integrate
    real engineering calculations.
    """

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """
        Perform structural sizing. Accepts `generate_structural` or `structural`
        as task IDs. If no panels exist the task completes with no patch.
        """
        tid = tid.lower().strip()
        if tid not in {"generate_structural", "structural"}:
            return {
                "card": {
                    "title": "Structural design",
                    "body": f"Unknown structural task '{tid}'.",
                },
                "patch": None,
                "status": "pending",
            }
        graph = await get_graph(session_id)
        if not graph:
            return {
                "card": {"title": "Structural design", "body": "Session not found."},
                "patch": None,
                "status": "pending",
            }
        panel_nodes = [n for n, data in graph.nodes(data=True) if data.get("type") == "panel"]
        if not panel_nodes:
            return {
                "card": {
                    "title": "Structural design",
                    "body": "No panels present; structural sizing skipped.",
                },
                "patch": None,
                "status": "complete",
            }
        add_nodes: List[ODLNode] = []
        add_edges: List[ODLEdge] = []
        for node_id in panel_nodes:
            mount_id = f"mount_{node_id}"
            add_nodes.append(ODLNode(id=mount_id, type="mount", data={"max_load_kN": 50.0}))
            add_edges.append(ODLEdge(source=mount_id, target=node_id, data={"type": "mounted_on"}))
        patch = GraphPatch(add_nodes=add_nodes, add_edges=add_edges).dict()
        return {
            "card": {
                "title": "Structural design",
                "body": f"Added {len(panel_nodes)} mount(s) for panels.",
            },
            "patch": patch,
            "status": "complete",
        }
