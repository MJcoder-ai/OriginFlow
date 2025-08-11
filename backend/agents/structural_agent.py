"""Structural agent for generating mounting hardware."""
from __future__ import annotations

from typing import Dict, List

from backend.services import odl_graph_service


class StructuralAgent:
    """Generate basic mounting hardware for panels."""

    def __init__(self) -> None:
        self.odl_graph_service = odl_graph_service

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """
        Generate mounting hardware for each panel in the design.  For each
        panel node, create a corresponding mount node and a physical
        'mounted_on' edge between the mount and the panel.  Uses a fixed
        mount specification for now and returns a complete status.
        """
        graph = await self.odl_graph_service.get_graph(session_id)
        mounts: List[Dict] = []
        edges: List[Dict] = []
        for node_id, data in graph.nodes(data=True):
            if data.get("type") == "panel":
                mount_id = f"mount_{node_id}"
                mounts.append(
                    {
                        "id": mount_id,
                        "data": {
                            "type": "mount",
                            "layer": "structural",
                            "max_load": 50.0,
                        },
                    }
                )
                edges.append(
                    {
                        "source": mount_id,
                        "target": node_id,
                        "data": {"type": "mounted_on"},
                    }
                )
        if not mounts:
            return {
                "card": {
                    "title": "Structural design",
                    "body": "No panels found; nothing to mount.",
                },
                "patch": None,
                "status": "complete",
            }
        patch = {"add_nodes": mounts, "add_edges": edges}
        return {
            "card": {
                "title": "Structural design",
                "body": f"Added {len(mounts)} mounts for {len(mounts)} panel(s).",
            },
            "patch": patch,
            "status": "complete",
        }
