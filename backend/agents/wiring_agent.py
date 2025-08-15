"""Wiring agent for generating cables and protective devices."""
from __future__ import annotations

from typing import Dict, List

from backend.services import odl_graph_service
from backend.services.placeholder_components import get_placeholder_service
from backend.utils.adpf import wrap_response
from backend.schemas.odl import ODLNode, ODLEdge


class WiringAgent:
    """
    Agent responsible for wiring design. For each electrical connection between
    a panel and an inverter this agent adds a cable and a protective fuse,
    connecting them with appropriate edge types.
    """
    
    def __init__(self):
        self.odl_graph_service = odl_graph_service
        self.placeholder_service = get_placeholder_service()

    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """
        Perform wiring sizing.  Accepts `generate_wiring` or `wiring` as task IDs
        and returns an ADPF envelope summarising the added components.
        """
        try:
            tid = tid.lower().strip()
            if tid not in {"generate_wiring", "wiring"}:
                return wrap_response(
                    thought=f"Received unknown wiring task '{tid}'.",
                    card={
                        "title": "Wiring design",
                        "body": f"Unknown wiring task '{tid}'.",
                    },
                    patch=None,
                    status="pending",
                )
            
            graph = await self.odl_graph_service.get_graph(session_id)
            if graph is None:
                return wrap_response(
                    thought="Cannot design wiring because the session does not exist.",
                    card={"title": "Wiring design", "body": "Session not found."},
                    patch=None,
                    status="blocked",
                )
            
            # Find electrical connections that need wiring
            electrical_edges = [(u, v, e_data) for u, v, e_data in graph.edges(data=True) 
                              if e_data.get("type") == "electrical" and not e_data.get("provisional")]
            
            if not electrical_edges:
                return wrap_response(
                    thought="No electrical connections present, so wiring cannot be generated.",
                    card={
                        "title": "Wiring design",
                        "body": "No electrical connections found. Generate design first.",
                    },
                    patch=None,
                    status="blocked",
                )
            
            # Check if wiring already exists
            existing_cables = [n for n, d in graph.nodes(data=True) 
                             if d.get("type") in ["cable", "generic_cable"]]
            existing_fuses = [n for n, d in graph.nodes(data=True) 
                            if d.get("type") in ["fuse", "generic_fuse"]]
            
            if existing_cables or existing_fuses:
                return wrap_response(
                    thought="Wiring already exists; skipping generation.",
                    card={
                        "title": "Wiring design",
                        "body": f"Wiring already exists ({len(existing_cables)} cables, {len(existing_fuses)} fuses).",
                    },
                    patch=None,
                    status="complete",
                )
            
            add_nodes: List[ODLNode] = []
            add_edges: List[ODLEdge] = []
            
            for u, v, e_data in electrical_edges:
                cable_id = f"cable_{u}_{v}"
                fuse_id = f"fuse_{u}_{v}"
                
                # Create placeholder cable
                cable_node = self.placeholder_service.create_placeholder_node(
                    node_id=cable_id,
                    component_type="generic_cable",
                    custom_attributes={
                        "connection_from": u,
                        "connection_to": v
                    },
                    layer="wiring"
                )
                add_nodes.append(ODLNode(**cable_node))
                
                # Create placeholder fuse
                fuse_node = self.placeholder_service.create_placeholder_node(
                    node_id=fuse_id,
                    component_type="generic_fuse",
                    custom_attributes={
                        "protects": cable_id
                    },
                    layer="wiring"
                )
                add_nodes.append(ODLNode(**fuse_node))
                
                # Create wiring connections
                add_edges.extend([
                    ODLEdge(source=u, target=fuse_id, data={"type": "protected_by"}, connection_type="electrical"),
                    ODLEdge(source=fuse_id, target=cable_id, data={"type": "connected_via"}, connection_type="electrical"),
                    ODLEdge(source=cable_id, target=v, data={"type": "terminates_at"}, connection_type="electrical"),
                ])
            
            if not add_nodes:
                return wrap_response(
                    thought="No electrical connections found; nothing to wire.",
                    card={
                        "title": "Wiring design",
                        "body": "No electrical connections found to wire.",
                    },
                    patch=None,
                    status="complete",
                )
            
            patch = {
                "add_nodes": [n.model_dump() for n in add_nodes],
                "add_edges": [e.model_dump() for e in add_edges]
            }
            
            cables_count = len([n for n in add_nodes if "cable" in n.id])
            fuses_count = len([n for n in add_nodes if "fuse" in n.id])
            
            card = {
                "title": "Wiring design",
                "body": f"Added {cables_count} cable(s) and {fuses_count} protective device(s).",
                "confidence": 0.7,
                "specs": [
                    {"label": "Cables Added", "value": str(cables_count), "confidence": 0.7},
                    {"label": "Fuses Added", "value": str(fuses_count), "confidence": 0.7},
                    {"label": "Wire Type", "value": "Generic placeholder", "confidence": 0.6}
                ],
                "actions": [
                    {"label": "Accept Wiring", "command": "accept_wiring", "variant": "primary", "icon": "check"},
                    {"label": "Customize Wiring", "command": "customize_wiring", "variant": "secondary", "icon": "edit"}
                ],
                "warnings": ["Using generic wiring - upload cable/fuse datasheets for real components"],
                "recommendations": ["Consider voltage drop calculations for final design"]
            }
            
            return wrap_response(
                thought=f"Added {cables_count} cable(s) and {fuses_count} protective device(s).",
                card=card,
                patch=patch,
                status="complete",
                warnings=card.get("warnings"),
            )
            
        except Exception as e:
            return wrap_response(
                thought="Encountered an exception during wiring design.",
                card={
                    "title": "Wiring design",
                    "body": f"Error generating wiring: {str(e)}",
                },
                patch=None,
                status="blocked",
            )
