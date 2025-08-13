"""Structural design agent for mounting systems."""
from __future__ import annotations

from typing import Dict, List
from backend.services import odl_graph_service
from backend.services.placeholder_components import get_placeholder_service
from backend.schemas.odl import ODLNode, ODLEdge


class StructuralAgent:
    """Agent responsible for structural design and mounting systems."""
    
    def __init__(self):
        self.odl_graph_service = odl_graph_service
        self.placeholder_service = get_placeholder_service()
    
    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """Execute structural design task."""
        try:
            if tid.lower().strip() not in {"generate_structural", "structural"}:
                return {
                    "card": {
                        "title": "Structural design",
                        "body": f"Unknown structural task '{tid}'.",
                    },
                    "patch": None,
                    "status": "pending",
                }
            
            graph = await self.odl_graph_service.get_graph(session_id)
            if not graph:
                return {
                    "card": {"title": "Structural design", "body": "Session not found."},
                    "patch": None,
                    "status": "blocked",
                }
            
            # Find panels that need mounting
            panels = [(n, d) for n, d in graph.nodes(data=True) 
                     if d.get("type") in ["panel", "generic_panel"]]
            
            if not panels:
                return {
                    "card": {
                        "title": "Structural design",
                        "body": "No panels found. Generate design first.",
                    },
                    "patch": None,
                    "status": "blocked",
                }
            
            # Check if mounts already exist
            existing_mounts = [n for n, d in graph.nodes(data=True) 
                             if d.get("type") in ["mount", "generic_mount"]]
            
            if existing_mounts:
                return {
                    "card": {
                        "title": "Structural design", 
                        "body": f"Mounting structure already exists ({len(existing_mounts)} mounts).",
                    },
                    "patch": None,
                    "status": "complete",
                }
            
            # Generate mounting for each panel
            nodes = []
            edges = []
            
            for i, (panel_id, panel_data) in enumerate(panels):
                mount_id = f"mount_{panel_id}"
                
                # Create mount node (placeholder for now)
                mount_node = self.placeholder_service.create_placeholder_node(
                    node_id=mount_id,
                    component_type="generic_mount",
                    custom_attributes={
                        "panels_supported": 1,
                        "panel_reference": panel_id
                    },
                    layer=panel_data.get("layer", "structural")
                )
                nodes.append(ODLNode(**mount_node))
                
                # Connect panel to mount
                edge = ODLEdge(
                    source=mount_id,
                    target=panel_id,
                    data={"type": "mechanical", "connection": "mounted"},
                    connection_type="mechanical"
                )
                edges.append(edge)
            
            patch = {
                "add_nodes": [n.model_dump() for n in nodes],
                "add_edges": [e.model_dump() for e in edges]
            }
            
            card = {
                "title": "Structural design",
                "body": f"Generated mounting structure for {len(panels)} panels.",
                "confidence": 0.8,
                "specs": [
                    {"label": "Mounts Created", "value": str(len(panels)), "confidence": 0.8},
                    {"label": "Mount Type", "value": "Generic placeholder", "confidence": 0.6}
                ],
                "actions": [
                    {"label": "Accept Mounting", "command": "accept_structural", "variant": "primary", "icon": "check"},
                    {"label": "Customize Mounts", "command": "customize_mounts", "variant": "secondary", "icon": "edit"}
                ],
                "warnings": ["Using generic mounting - upload mount datasheets for real components"],
                "recommendations": ["Consider wind and snow loads for final design"]
            }
            
            return {
                "card": card,
                "patch": patch,
                "status": "complete",
            }
            
        except Exception as e:
            return {
                "card": {
                    "title": "Structural design",
                    "body": f"Error generating structural design: {str(e)}",
                },
                "patch": None,
                "status": "blocked",
            }