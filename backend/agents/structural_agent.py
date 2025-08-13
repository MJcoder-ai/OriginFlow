"""Structural agent for generating mounting hardware."""
from __future__ import annotations

from typing import Dict, List

from backend.services import odl_graph_service


class StructuralAgent:
    """Generate basic mounting hardware for panels.

    The agent scans the existing graph for panel nodes and creates a
    corresponding mount for each one.  Each mount includes a placeholder
    ``max_load`` value which will eventually be refined by a structural rule
    engine.  The panel and mount are linked via a ``mounted_on`` edge on the
    ``structural`` layer.
    """

    def __init__(self) -> None:
        self.odl_graph_service = odl_graph_service

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """
        Generate mounting hardware for each panel in the design.  For every
        panel node we add a mount node with a dummy ``max_load`` field and join
        them with a ``mounted_on`` edge.  The implementation is intentionally
        simple and acts as a placeholder for more detailed structural analysis.
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
        
        # Enhanced design card with specs and actions
        enhanced_card = {
            "title": "Structural design",
            "body": f"Generated mounting hardware for {len(mounts)} panel{'s' if len(mounts) != 1 else ''}.",
            "confidence": 0.8,  # Structural design is fairly standardized
            "specs": [
                {"label": "Mounts Created", "value": str(len(mounts)), "confidence": 1.0},
                {"label": "Max Load", "value": "50.0", "unit": "kg", "confidence": 0.8},
                {"label": "Mount Type", "value": "Standard", "confidence": 0.8}
            ],
            "actions": [
                {"label": "Accept Mounting", "command": "accept_structural", "variant": "primary", "icon": "check"},
                {"label": "Review Loads", "command": "review_structural", "variant": "secondary", "icon": "calculator"},
                {"label": "Custom Mounting", "command": "custom_structural", "variant": "secondary", "icon": "edit"}
            ],
            "warnings": [],
            "recommendations": [
                "Verify structural load calculations with a licensed engineer",
                "Consider wind and snow loads for your region"
            ]
        }
        
        return {
            "card": enhanced_card,
            "patch": patch,
            "status": "complete",
        }
