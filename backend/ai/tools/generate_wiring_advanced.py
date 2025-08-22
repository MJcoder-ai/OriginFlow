"""
Advanced wiring generation tool for solar systems.
Integrates component library, topology engine, and auto-routing.
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from backend.solar.components import components, ComponentCategory
from backend.solar.topologies import create_topology_engine, SystemDesignParameters, SystemTopology, ProtectionLevel
from backend.solar.routing import Router
from backend.odl.schemas import ODLGraph, ODLNode, ODLEdge

logger = logging.getLogger(__name__)

async def generate_wiring_advanced(
    graph: ODLGraph,
    session_id: str,
    layer: str = "single-line",
    system_type: str = "string_inverter",
    protection_level: str = "standard",
    **kwargs
) -> Dict[str, Any]:
    """
    Advanced wiring generation for solar systems.
    
    Args:
        graph: Current ODL graph
        session_id: Session identifier
        layer: Target layer for wiring
        system_type: Type of system topology
        protection_level: Level of electrical protection
        **kwargs: Additional parameters
    
    Returns:
        Dictionary with wiring results and system design
    """
    
    logger.info(f"Generating enhanced wiring for session {session_id}")
    
    try:
        # Analyze existing components in the graph
        component_analysis = _analyze_graph_components(graph, layer)
        
        if not component_analysis["has_modules"] or not component_analysis["has_inverters"]:
            return {
                "success": False,
                "message": "Need at least 1 PV module and 1 inverter for wiring generation",
                "analysis": component_analysis
            }
        
        # Create system design parameters
        system_params = _create_system_parameters(
            component_analysis, system_type, protection_level, kwargs
        )
        
        # Generate system topology
        topology_engine = create_topology_engine()
        available_components = _get_available_component_ids(component_analysis)
        
        system_design = topology_engine.design_system_topology(
            system_params, available_components
        )
        
        # Extract component positions from graph
        component_positions, component_mapping = _extract_component_positions(graph, layer)
        
        # Generate intelligent routing
        router = Router(components, topology_engine)
        routing = router.generate_complete_system_routing(system_design, component_positions)
        
        # Apply wiring to the graph
        wiring_results = _apply_wiring_to_graph(
            graph, system_design, routing, layer, session_id, component_mapping
        )
        
        # Generate comprehensive documentation
        documentation = _generate_system_documentation(system_design, routing)
        
        return {
            "success": True,
            "message": f"Generated {system_type} wiring with {len(routing)} connections",
            "system_design": system_design,
            "routing": [asdict(route) for route in routing],
            "wiring_applied": wiring_results,
            "documentation": documentation,
            "analysis": component_analysis
        }
        
    except Exception as e:
        logger.error(f"Enhanced wiring generation failed: {e}")
        return {
            "success": False,
            "message": f"Wiring generation failed: {str(e)}",
            "error_type": type(e).__name__
        }

def _analyze_graph_components(graph: ODLGraph, layer: str) -> Dict[str, Any]:
    """Analyze components present in the graph"""
    
    analysis = {
        "total_nodes": len(graph.nodes),
        "layer_nodes": 0,
        "has_modules": False,
        "has_inverters": False,
        "has_protection_devices": False,
        "components_by_type": {},
        "total_power_estimate": 0.0,
        "module_count": 0,
        "inverter_count": 0
    }
    
    for node in graph.nodes.values():
        node_layer = node.attrs.get("layer") if node.attrs else None
        if node_layer != layer:
            continue
            
        analysis["layer_nodes"] += 1
        
        # Categorize components
        node_type = node.type.lower()
        
        if node_type not in analysis["components_by_type"]:
            analysis["components_by_type"][node_type] = 0
        analysis["components_by_type"][node_type] += 1
        
        # Check for key component types
        if "panel" in node_type or "module" in node_type:
            analysis["has_modules"] = True
            analysis["module_count"] += 1
            # Estimate power (assume 400W panels)
            analysis["total_power_estimate"] += 0.4
            
        elif "inverter" in node_type:
            analysis["has_inverters"] = True  
            analysis["inverter_count"] += 1
            
        elif any(term in node_type for term in ["disconnect", "breaker", "fuse", "combiner"]):
            analysis["has_protection_devices"] = True
    
    logger.info(f"Graph analysis: {analysis}")
    return analysis

def _create_system_parameters(component_analysis: Dict[str, Any], 
                            system_type: str, protection_level: str,
                            kwargs: Dict[str, Any]) -> SystemDesignParameters:
    """Create system design parameters from analysis"""
    
    # Map string parameters to enums
    topology_map = {
        "string_inverter": SystemTopology.STRING_INVERTER,
        "power_optimizer": SystemTopology.POWER_OPTIMIZER,
        "microinverter": SystemTopology.MICROINVERTER,
        "commercial": SystemTopology.COMMERCIAL_THREE_PHASE,
        "battery": SystemTopology.BATTERY_STORAGE
    }
    
    protection_map = {
        "basic": ProtectionLevel.BASIC,
        "standard": ProtectionLevel.STANDARD,
        "enhanced": ProtectionLevel.ENHANCED,
        "critical": ProtectionLevel.CRITICAL
    }
    
    topology = topology_map.get(system_type.lower(), SystemTopology.STRING_INVERTER)
    protection = protection_map.get(protection_level.lower(), ProtectionLevel.STANDARD)
    
    # Determine system voltage based on size
    total_power = component_analysis.get("total_power_estimate", 5.0)
    if total_power >= 50:  # Large commercial
        voltage_system = "480V_3P"
    elif total_power >= 10:  # Small commercial
        voltage_system = "208V_3P" 
    else:  # Residential
        voltage_system = "240V_1P"
    
    return SystemDesignParameters(
        total_power_kw=total_power,
        voltage_system=voltage_system,
        topology=topology,
        protection_level=protection,
        temperature_ambient_max=kwargs.get("ambient_temp", 40.0),
        temperature_module_max=kwargs.get("module_temp", 70.0),
        nec_version=kwargs.get("nec_version", "2020"),
        string_sizing_strategy=kwargs.get("string_strategy", "voltage_optimized"),
        combiner_preference=kwargs.get("use_combiners", True),
        monitoring_level=kwargs.get("monitoring", "system")
    )

def _get_available_component_ids(component_analysis: Dict[str, Any]) -> List[str]:
    """Get list of available component IDs for system design"""
    
    # Map discovered components to library IDs
    available = []
    
    components_by_type = component_analysis.get("components_by_type", {})
    
    # Add modules
    if any("panel" in t or "module" in t for t in components_by_type):
        available.append("pv_module_400w")
    
    # Add inverters
    if any("inverter" in t for t in components_by_type):
        available.append("string_inverter_10kw")
    
    # Add standard protection devices (always available)
    available.extend([
        "dc_combiner_6string",
        "dc_disconnect_60a", 
        "ac_breaker_40a_3p",
        "production_meter"
    ])
    
    return available

def _extract_component_positions(graph: ODLGraph, layer: str) -> tuple[Dict[str, tuple], Dict[str, str]]:
    """Extract component positions from the graph and return mapping"""
    
    positions = {}
    component_mapping = {}  # maps routing_id -> odl_node_id
    
    for node_id, node in graph.nodes.items():
        node_layer = node.attrs.get("layer") if node.attrs else None
        if node_layer != layer:
            continue
        
        # Get position from node attributes
        x = 0.0
        y = 0.0
        
        if node.attrs:
            x = float(node.attrs.get("x", 0))
            y = float(node.attrs.get("y", 0))
        
        # Map to component naming convention
        node_type = node.type.lower()
        if "panel" in node_type or "module" in node_type:
            # Count existing modules to determine index
            module_count = sum(1 for pos_key in positions.keys() if pos_key.startswith("module_"))
            component_key = f"module_{module_count + 1}"
        elif "inverter" in node_type:
            inverter_count = sum(1 for pos_key in positions.keys() if pos_key.startswith("inverter_"))
            component_key = f"inverter_{inverter_count + 1}"
        else:
            component_key = node_type
        
        positions[component_key] = (x, y)
        component_mapping[component_key] = node_id
    
    return positions, component_mapping

def _apply_wiring_to_graph(graph: ODLGraph, system_design: Dict[str, Any],
                         routing: List, layer: str, session_id: str, 
                         component_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Apply generated wiring to the ODL graph"""
    
    results = {
        "edges_added": 0,
        "nodes_added": 0,
        "protection_devices_added": 0,
        "warnings": []
    }
    
    # Add protection device nodes
    protection_devices = system_design.get("protection_devices", {})
    for device_id, device_info in protection_devices.items():
        if "component_id" in device_info:
            device_component = components.get_component(device_info["component_id"])
            if device_component:
                # Find a good position (simplified - could use intelligent placement)
                device_x = 400 + results["nodes_added"] * 50
                device_y = 200
                
                device_node = ODLNode(
                    id=device_id,
                    type=device_component.category.value,
                    attrs={
                        "layer": layer,
                        "x": device_x,
                        "y": device_y,
                        "manufacturer": device_component.manufacturer,
                        "model": device_component.model_number,
                        "nec_article": device_component.nec_article,
                        "certifications": device_component.certifications
                    }
                )
                
                graph.nodes[device_id] = device_node
                results["nodes_added"] += 1
                results["protection_devices_added"] += 1
    
    # Add wiring connections as edges
    for route in routing:
        # Map routing component IDs to actual ODL node IDs
        source_node_id = component_mapping.get(route.source_component)
        target_node_id = component_mapping.get(route.target_component)
        
        # Skip if source or target components don't exist in mapping or graph
        if not source_node_id or not target_node_id:
            results["warnings"].append(f"Skipping route {route.route_id}: component not in mapping")
            continue
            
        if source_node_id not in graph.nodes or target_node_id not in graph.nodes:
            results["warnings"].append(f"Skipping route {route.route_id}: missing components")
            continue
        
        # Create edge ID
        edge_id = f"{source_node_id}_{target_node_id}_{route.route_id}"
        
        # Create ODL edge
        edge = ODLEdge(
            id=edge_id,
            source_id=source_node_id,
            target_id=target_node_id,
            kind="electrical",
            attrs={
                "layer": layer,
                "route_type": route.route_type.value,
                "voltage_type": route.voltage_type,
                "max_voltage": route.max_voltage,
                "max_current": route.max_current,
                "wire_type": route.wire_type,
                "wire_size": route.wire_size,
                "conduit_type": route.conduit_type,
                "conduit_size": route.conduit_size,
                "nec_article": route.nec_article,
                "installation_method": route.installation_method,
                "source_port": route.source_port,
                "target_port": route.target_port
            }
        )
        
        graph.edges.append(edge)
        results["edges_added"] += 1
    
    logger.info(f"Applied wiring to graph: {results}")
    return results

def _generate_system_documentation(system_design: Dict[str, Any], 
                                 routing: List) -> Dict[str, Any]:
    """Generate comprehensive system documentation"""
    
    documentation = {
        "system_summary": {
            "topology": system_design.get("topology"),
            "total_power_kw": system_design.get("summary", {}).get("total_power_kw"),
            "total_modules": system_design.get("summary", {}).get("total_modules"),
            "num_strings": system_design.get("summary", {}).get("num_strings"),
            "protection_level": "standard"
        },
        
        "bill_of_materials": _generate_bill_of_materials(system_design),
        
        "installation_checklist": [
            "Verify all components match specifications",
            "Check local permitting requirements",
            "Confirm utility interconnection agreement",
            "Install DC disconnect within sight of inverter",
            "Label all DC circuits per NEC 690.31(G)",
            "Install equipment grounding per NEC 690.43",
            "Configure rapid shutdown per NEC 690.12",
            "Test system operation and monitoring",
            "Submit final documentation to AHJ"
        ],
        
        "code_compliance": system_design.get("code_compliance", {}),
        
        "wiring_summary": {
            "total_routes": len(routing),
            "dc_circuits": len([r for r in routing if r.voltage_type == "dc"]),
            "ac_circuits": len([r for r in routing if r.voltage_type == "ac"]),
            "grounding_circuits": len([r for r in routing if r.route_type.value == "ground"]),
            "data_circuits": len([r for r in routing if r.route_type.value == "data"])
        },
        
        "safety_warnings": [
            "De-energize all circuits before making connections",
            "Verify proper polarity on all DC connections",
            "Use appropriate personal protective equipment",
            "Follow manufacturer torque specifications",
            "Test all connections with appropriate meters",
            "Ensure all equipment is properly grounded"
        ]
    }
    
    return documentation

def _generate_bill_of_materials(system_design: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate bill of materials from system design"""
    
    bom = []
    
    # Add main components
    for component_type, component_info in system_design.get("components", {}).items():
        if "component_id" in component_info:
            component = components.get_component(component_info["component_id"])
            if component:
                bom.append({
                    "category": component.category.value,
                    "description": component.name,
                    "manufacturer": component.manufacturer,
                    "model_number": component.model_number,
                    "quantity": component_info.get("quantity", 1),
                    "unit_cost": component.cost_estimate,
                    "certifications": component.certifications
                })
    
    # Add protection devices
    for device_id, device_info in system_design.get("protection_devices", {}).items():
        if "component_id" in device_info:
            component = components.get_component(device_info["component_id"])
            if component:
                bom.append({
                    "category": component.category.value,
                    "description": component.name,
                    "manufacturer": component.manufacturer, 
                    "model_number": component.model_number,
                    "quantity": device_info.get("quantity", 1),
                    "unit_cost": component.cost_estimate,
                    "certifications": component.certifications
                })
    
    return bom