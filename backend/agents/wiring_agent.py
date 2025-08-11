"""Wiring agent for generating cables and protective devices."""
from __future__ import annotations

from typing import Dict, List

from backend.services import odl_graph_service


class WiringAgent:
    """Generate basic wiring components between panels and inverters."""

    def __init__(self) -> None:
        self.odl_graph_service = odl_graph_service

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """
        Generate wiring for a preliminary design.  For each panel connected to
        an inverter, create a cable node and a protective device, and connect
        them accordingly.  Uses simplified current and voltage calculations.
        """
        graph = await self.odl_graph_service.get_graph(session_id)
        cables: List[Dict] = []
        devices: List[Dict] = []
        edges: List[Dict] = []
        for u, v, data in graph.edges(data=True):
            if data.get("type") == "electrical":
                cable_id = f"cable_{u}_{v}"
                cables.append(
                    {
                        "id": cable_id,
                        "data": {
                            "type": "cable",
                            "layer": "wiring",
                            "gauge": "10 AWG",
                        },
                    }
                )
                fuse_id = f"fuse_{u}_{v}"
                devices.append(
                    {
                        "id": fuse_id,
                        "data": {
                            "type": "fuse",
                            "layer": "wiring",
                            "rating": 15.0,
                        },
                    }
                )
                edges.extend(
                    [
                        {"source": u, "target": fuse_id, "data": {"type": "protected_by"}},
                        {"source": fuse_id, "target": cable_id, "data": {"type": "connected_via"}},
                        {"source": cable_id, "target": v, "data": {"type": "terminates_at"}},
                    ]
                )
        if not cables:
            return {
                "card": {
                    "title": "Wiring design",
                    "body": "No electrical connections found; nothing to wire.",
                },
                "patch": None,
                "status": "complete",
            }
        patch = {"add_nodes": cables + devices, "add_edges": edges}
        return {
            "card": {
                "title": "Wiring design",
                "body": f"Added {len(cables)} cables and {len(devices)} protective devices.",
            },
            "patch": patch,
            "status": "complete",
        }
