"""Wiring agent for generating cables and protective devices."""
from __future__ import annotations

from typing import Dict, List

from backend.services.odl_graph_service import get_graph
from backend.schemas.odl import ODLNode, ODLEdge, GraphPatch


class WiringAgent:
    """
    Agent responsible for wiring design. For each electrical connection between
    a panel and an inverter this agent adds a cable and a protective fuse,
    connecting them with appropriate edge types.
    """

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """
        Perform wiring sizing. Accepts `generate_wiring` or `wiring` as task IDs
        and returns a card summarising any added components.
        """
        tid = tid.lower().strip()
        if tid not in {"generate_wiring", "wiring"}:
            return {
                "card": {
                    "title": "Wiring design",
                    "body": f"Unknown wiring task '{tid}'.",
                },
                "patch": None,
                "status": "pending",
            }
        graph = await get_graph(session_id)
        if not graph:
            return {
                "card": {"title": "Wiring design", "body": "Session not found."},
                "patch": None,
                "status": "pending",
            }
        add_nodes: List[ODLNode] = []
        add_edges: List[ODLEdge] = []
        for u, v, e_data in graph.edges(data=True):
            if e_data.get("type") == "electrical":
                cable_id = f"cable_{u}_{v}"
                fuse_id = f"fuse_{u}_{v}"
                add_nodes.append(ODLNode(id=cable_id, type="cable", data={"gauge": "10AWG", "length_m": 10.0}))
                add_nodes.append(ODLNode(id=fuse_id, type="fuse", data={"rating_A": 15.0}))
                add_edges.extend([
                    ODLEdge(source=u, target=fuse_id, data={"type": "protected_by"}),
                    ODLEdge(source=fuse_id, target=cable_id, data={"type": "connected_via"}),
                    ODLEdge(source=cable_id, target=v, data={"type": "terminates_at"}),
                ])
        if not add_nodes:
            return {
                "card": {
                    "title": "Wiring design",
                    "body": "No panel–inverter connections found; wiring skipped.",
                },
                "patch": None,
                "status": "complete",
            }
        patch = GraphPatch(add_nodes=add_nodes, add_edges=add_edges).dict()
        return {
            "card": {
                "title": "Wiring design",
                "body": f"Added {len(add_nodes)//2} cable(s) and protective device(s).",
            },
            "patch": patch,
            "status": "complete",
        }
