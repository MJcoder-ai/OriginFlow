"""
Protective device insertion tools.

Pure functions for adding DC switches, disconnects, breakers, and fuses
to existing electrical designs. Handles both standalone placement and
series insertion between existing components.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
import uuid

from backend.odl.schemas import PatchOp, ODLNode, ODLEdge
from .schemas import AddProtectiveDeviceInput, make_patch


def add_protective_device(inp: AddProtectiveDeviceInput):
    """
    Add a protective device to the design.
    
    For series_insertion mode: finds existing connections and inserts the device
    For standalone mode: just adds the device as a new component
    """
    ops = []
    device_id = f"{inp.device_type}:{inp.request_id}:1"
    
    # Create the protective device node
    device_attrs = {
        "layer": inp.layer,
        "placeholder": True,
        "device_type": inp.device_type,
    }
    
    # Add ratings if specified
    if inp.rating_A:
        device_attrs["rating_A"] = inp.rating_A
    if inp.voltage_rating_V:
        device_attrs["voltage_rating_V"] = inp.voltage_rating_V
    
    # Determine device position based on existing components
    x, y = _calculate_device_position(inp.view_nodes, inp.connection_mode)
    device_attrs.update({"x": x, "y": y})
    
    # Add the device node
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:node:{inp.device_type}",
            op="add_node",
            value={
                "id": device_id,
                "type": inp.device_type,
                "attrs": device_attrs,
            },
        )
    )
    
    if inp.connection_mode == "series_insertion":
        # Find existing connections to interrupt
        connections_to_modify = _find_insertion_points(inp.view_nodes, inp.existing_components)
        
        for i, (source_node, target_node, existing_edge) in enumerate(connections_to_modify):
            # Remove the original connection
            if existing_edge:
                ops.append(
                    PatchOp(
                        op_id=f"{inp.request_id}:remove_edge:{i}",
                        op="remove_edge",
                        value=existing_edge.id,
                    )
                )
            
            # Add connection from source to protective device
            ops.append(
                PatchOp(
                    op_id=f"{inp.request_id}:edge:in:{i}",
                    op="add_edge",
                    value={
                        "id": f"edge:{source_node.id}:{device_id}:{i}",
                        "source_id": source_node.id,
                        "target_id": device_id,
                        "kind": "electrical",
                        "attrs": {"layer": inp.layer, "connection_type": "dc"},
                    },
                )
            )
            
            # Add connection from protective device to target
            ops.append(
                PatchOp(
                    op_id=f"{inp.request_id}:edge:out:{i}",
                    op="add_edge",
                    value={
                        "id": f"edge:{device_id}:{target_node.id}:{i}",
                        "source_id": device_id,
                        "target_id": target_node.id,
                        "kind": "electrical",
                        "attrs": {"layer": inp.layer, "connection_type": "dc"},
                    },
                )
            )
    
    # Add annotation describing what was done
    ops.append(
        PatchOp(
            op_id=f"{inp.request_id}:ann:device",
            op="add_edge",
            value={
                "id": f"ann:device:{inp.request_id}",
                "source_id": "__decision__",
                "target_id": "__design__",
                "kind": "annotation",
                "attrs": {
                    "tool": "add_protective_device",
                    "result": {
                        "device_type": inp.device_type,
                        "device_id": device_id,
                        "connection_mode": inp.connection_mode,
                        "connections_modified": len(connections_to_modify) if inp.connection_mode == "series_insertion" else 0
                    }
                },
            },
        )
    )
    
    return make_patch(inp.request_id, ops)


def _calculate_device_position(view_nodes: List[ODLNode], connection_mode: str) -> Tuple[float, float]:
    """Calculate where to position the protective device"""
    if not view_nodes:
        return (200.0, 200.0)  # Default position
    
    if connection_mode == "series_insertion":
        # Position between existing components
        panels = [n for n in view_nodes if "panel" in n.type.lower()]
        inverters = [n for n in view_nodes if "inverter" in n.type.lower()]
        
        if panels and inverters:
            # Position between first panel and first inverter
            panel = panels[0]
            inverter = inverters[0]
            panel_x = panel.attrs.get("x", 100) if panel.attrs else 100
            panel_y = panel.attrs.get("y", 100) if panel.attrs else 100
            inverter_x = inverter.attrs.get("x", 300) if inverter.attrs else 300
            inverter_y = inverter.attrs.get("y", 100) if inverter.attrs else 100
            
            # Position midway between panel and inverter
            mid_x = (panel_x + inverter_x) / 2
            mid_y = (panel_y + inverter_y) / 2
            return (mid_x, mid_y)
    
    # Default: position to the right of existing components
    max_x = max((n.attrs.get("x", 0) if n.attrs else 0) for n in view_nodes)
    avg_y = sum((n.attrs.get("y", 100) if n.attrs else 100) for n in view_nodes) / len(view_nodes)
    return (max_x + 100, avg_y)


def _find_insertion_points(view_nodes: List[ODLNode], existing_components: List[str]) -> List[Tuple[ODLNode, ODLNode, Optional[ODLEdge]]]:
    """
    Find connection points where protective device should be inserted.
    Returns list of (source_node, target_node, existing_edge) tuples.
    """
    # For now, implement a simple strategy: find panel->inverter connections
    panels = [n for n in view_nodes if "panel" in n.type.lower()]
    inverters = [n for n in view_nodes if "inverter" in n.type.lower()]
    
    connections = []
    
    # Simple case: if we have panels and inverters, insert between them
    if panels and inverters:
        # For each panel, find its connection to an inverter
        # This is a simplified implementation - in practice you'd need to trace edges
        for panel in panels[:1]:  # Just first panel for now
            for inverter in inverters[:1]:  # Just first inverter for now
                connections.append((panel, inverter, None))  # No existing edge tracking for now
                break
    
    return connections