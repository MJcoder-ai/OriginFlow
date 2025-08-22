"""
Auto-routing system for solar installations.
Generates wiring paths with protection devices and code compliance.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
import logging
import math
from enum import Enum

from .components import ComponentLibrary, ComponentDefinition, ComponentCategory
from .topologies import TopologyEngine, SystemDesignParameters, SystemTopology, ProtectionLevel

logger = logging.getLogger(__name__)

class RouteType(Enum):
    DC_STRING = "dc_string"
    DC_COMBINER = "dc_combiner"
    DC_MAIN = "dc_main"
    AC_INVERTER = "ac_inverter"
    AC_MAIN = "ac_main"
    GROUND = "ground"
    DATA = "data"

@dataclass
class RouteSegment:
    """A segment of electrical routing"""
    route_id: str
    route_type: RouteType
    source_component: str
    target_component: str
    source_port: str
    target_port: str
    
    # Electrical properties
    voltage_type: str  # "dc" or "ac"
    max_voltage: float
    max_current: float
    
    # Physical routing
    wire_type: str
    wire_size: str
    conduit_type: Optional[str] = None
    conduit_size: Optional[str] = None
    
    # Protection devices on this route
    protection_devices: List[str] = None
    
    # Code compliance
    nec_article: str = ""
    installation_method: str = ""  # "conduit", "cable_tray", "direct_burial"

@dataclass
class RoutingNode:
    """A node in the routing graph"""
    node_id: str
    component_id: str
    position: Tuple[float, float]
    available_ports: List[str]
    connected_ports: Set[str] = None

class Router:
    """Auto-routing system for solar installations"""
    
    def __init__(self, component_library: ComponentLibrary, topology_engine: TopologyEngine):
        self.component_library = component_library
        self.topology_engine = topology_engine
        self.wire_sizing_table = self._load_wire_sizing_table()
    
    def generate_complete_system_routing(self, system_design: Dict, 
                                       component_positions: Dict[str, Tuple[float, float]]) -> List[RouteSegment]:
        """Generate complete routing for a solar system design"""
        
        logger.info(f"Generating routing for {system_design.get('topology', 'unknown')} system")
        
        routes = []
        routing_nodes = self._create_routing_nodes(system_design, component_positions)
        
        # Generate routes based on system topology
        if system_design.get("topology") == "string_inverter":
            routes.extend(self._route_string_inverter_system(system_design, routing_nodes))
        elif system_design.get("topology") == "commercial_three_phase":
            routes.extend(self._route_commercial_system(system_design, routing_nodes))
        
        # Add grounding routes
        routes.extend(self._generate_grounding_routes(routing_nodes))
        
        # Add monitoring/data routes
        routes.extend(self._generate_data_routes(routing_nodes))
        
        # Optimize routing paths
        routes = self._optimize_routing_paths(routes, routing_nodes)
        
        # Add conduit and protection device routing
        routes = self._add_protection_device_routing(routes, system_design)
        
        return routes
    
    def _create_routing_nodes(self, system_design: Dict, 
                            component_positions: Dict[str, Tuple[float, float]]) -> Dict[str, RoutingNode]:
        """Create routing nodes for all components"""
        
        nodes = {}
        
        # Create nodes for modules
        if "modules" in system_design.get("components", {}):
            module_info = system_design["components"]["modules"]
            module_component = self.component_library.get_component(module_info["component_id"])
            
            for i in range(module_info["quantity"]):
                node_id = f"module_{i+1}"
                position = component_positions.get(node_id, (i * 100, 0))
                
                nodes[node_id] = RoutingNode(
                    node_id=node_id,
                    component_id=module_info["component_id"],
                    position=position,
                    available_ports=[port.id for port in module_component.ports],
                    connected_ports=set()
                )
        
        # Create nodes for inverters
        if "inverters" in system_design.get("components", {}):
            inverter_info = system_design["components"]["inverters"]
            inverter_component = self.component_library.get_component(inverter_info["component_id"])
            
            for i in range(inverter_info["quantity"]):
                node_id = f"inverter_{i+1}"
                position = component_positions.get(node_id, (500, 150))
                
                nodes[node_id] = RoutingNode(
                    node_id=node_id,
                    component_id=inverter_info["component_id"],
                    position=position,
                    available_ports=[port.id for port in inverter_component.ports],
                    connected_ports=set()
                )
        
        # Create nodes for combiners
        if "combiners" in system_design.get("components", {}):
            combiner_info = system_design["components"]["combiners"]
            combiner_component = self.component_library.get_component(combiner_info["component_id"])
            
            for i in range(combiner_info["quantity"]):
                node_id = f"combiner_{i+1}"
                position = component_positions.get(node_id, (300, 75))
                
                nodes[node_id] = RoutingNode(
                    node_id=node_id,
                    component_id=combiner_info["component_id"],
                    position=position,
                    available_ports=[port.id for port in combiner_component.ports],
                    connected_ports=set()
                )
        
        # Create nodes for protection devices
        for device_id, device_info in system_design.get("protection_devices", {}).items():
            if "component_id" in device_info:
                device_component = self.component_library.get_component(device_info["component_id"])
                if device_component:
                    for i in range(device_info.get("quantity", 1)):
                        node_id = f"{device_id}_{i+1}" if device_info.get("quantity", 1) > 1 else device_id
                        position = component_positions.get(node_id, (400, 200))
                        
                        nodes[node_id] = RoutingNode(
                            node_id=node_id,
                            component_id=device_info["component_id"],
                            position=position,
                            available_ports=[port.id for port in device_component.ports],
                            connected_ports=set()
                        )
        
        return nodes
    
    def _route_string_inverter_system(self, system_design: Dict, 
                                    routing_nodes: Dict[str, RoutingNode]) -> List[RouteSegment]:
        """Generate routing for string inverter system"""
        
        routes = []
        summary = system_design.get("summary", {})
        
        modules_per_string = summary.get("modules_per_string", 10)
        num_strings = summary.get("num_strings", 1)
        
        # Route PV strings
        for string_num in range(num_strings):
            string_routes = self._route_pv_string(
                string_num, modules_per_string, routing_nodes, system_design
            )
            routes.extend(string_routes)
        
        # Route combiner connections (if present)
        if "combiners" in system_design.get("components", {}):
            combiner_routes = self._route_combiner_connections(routing_nodes, system_design)
            routes.extend(combiner_routes)
        
        # Route DC main to inverter
        dc_main_routes = self._route_dc_main_connections(routing_nodes, system_design)
        routes.extend(dc_main_routes)
        
        # Route AC output
        ac_output_routes = self._route_ac_output_connections(routing_nodes, system_design)
        routes.extend(ac_output_routes)
        
        return routes
    
    def _route_pv_string(self, string_num: int, modules_per_string: int,
                        routing_nodes: Dict[str, RoutingNode], 
                        system_design: Dict) -> List[RouteSegment]:
        """Route a single PV string"""
        
        routes = []
        string_start = string_num * modules_per_string
        
        # Get module component for electrical specs
        module_info = system_design["components"]["modules"]
        module_component = self.component_library.get_component(module_info["component_id"])
        
        max_current = module_component.electrical_specs.current_max or 10
        max_voltage = (module_component.electrical_specs.voltage_dc_max or 48) * modules_per_string
        
        # Route modules in series
        for i in range(modules_per_string - 1):
            source_node = f"module_{string_start + i + 1}"
            target_node = f"module_{string_start + i + 2}"
            
            # Calculate wire size based on current and distance
            distance = self._calculate_distance(
                routing_nodes[source_node].position,
                routing_nodes[target_node].position
            )
            
            wire_size = self._calculate_wire_size(max_current, distance, voltage_drop_percent=3.0)
            
            route = RouteSegment(
                route_id=f"string_{string_num+1}_segment_{i+1}",
                route_type=RouteType.DC_STRING,
                source_component=source_node,
                target_component=target_node,
                source_port="dc_out_pos",
                target_port="dc_out_neg",  # Series connection: + to -
                voltage_type="dc",
                max_voltage=max_voltage,
                max_current=max_current,
                wire_type="PV Wire",
                wire_size=wire_size,
                nec_article="690.31",
                installation_method="conduit"
            )
            
            routes.append(route)
            
            # Mark ports as connected
            routing_nodes[source_node].connected_ports.add("dc_out_pos")
            routing_nodes[target_node].connected_ports.add("dc_out_neg")
        
        return routes
    
    def _route_combiner_connections(self, routing_nodes: Dict[str, RoutingNode],
                                   system_design: Dict) -> List[RouteSegment]:
        """Route string connections to combiner boxes"""
        
        routes = []
        summary = system_design.get("summary", {})
        modules_per_string = summary.get("modules_per_string", 10)
        num_strings = summary.get("num_strings", 1)
        
        # Get combiner component
        combiner_info = system_design["components"]["combiners"]
        combiner_component = self.component_library.get_component(combiner_info["component_id"])
        
        strings_per_combiner = 6  # Standard combiner capacity
        combiner_index = 0
        
        for string_num in range(num_strings):
            # Determine which combiner this string connects to
            if string_num > 0 and string_num % strings_per_combiner == 0:
                combiner_index += 1
            
            combiner_node = f"combiner_{combiner_index + 1}"
            if combiner_node not in routing_nodes:
                continue
            
            # Connect string output to combiner input
            last_module_in_string = f"module_{(string_num + 1) * modules_per_string}"
            
            if last_module_in_string not in routing_nodes:
                continue
            
            # Find available combiner input port
            input_port_num = (string_num % strings_per_combiner) + 1
            combiner_input_pos = f"dc_in_{input_port_num}_pos"
            combiner_input_neg = f"dc_in_{input_port_num}_neg"
            
            # Calculate routing parameters
            distance = self._calculate_distance(
                routing_nodes[last_module_in_string].position,
                routing_nodes[combiner_node].position
            )
            
            module_component = self.component_library.get_component(
                system_design["components"]["modules"]["component_id"]
            )
            max_current = module_component.electrical_specs.current_max or 10
            wire_size = self._calculate_wire_size(max_current, distance, voltage_drop_percent=2.0)
            
            # Positive route
            route_pos = RouteSegment(
                route_id=f"string_{string_num+1}_to_combiner_pos",
                route_type=RouteType.DC_COMBINER,
                source_component=last_module_in_string,
                target_component=combiner_node,
                source_port="dc_out_pos",
                target_port=combiner_input_pos,
                voltage_type="dc",
                max_voltage=modules_per_string * (module_component.electrical_specs.voltage_dc_max or 48),
                max_current=max_current,
                wire_type="THWN-2",
                wire_size=wire_size,
                nec_article="690.31",
                installation_method="conduit",
                protection_devices=[f"fuse_{input_port_num}"]  # String fuse protection
            )
            
            routes.append(route_pos)
            
            # Mark ports as connected
            routing_nodes[last_module_in_string].connected_ports.add("dc_out_pos")
            routing_nodes[combiner_node].connected_ports.add(combiner_input_pos)
        
        return routes
    
    def _route_dc_main_connections(self, routing_nodes: Dict[str, RoutingNode],
                                 system_design: Dict) -> List[RouteSegment]:
        """Route DC main connections from combiner to inverter"""
        
        routes = []
        
        # Find combiners and inverters
        combiner_nodes = [n for n in routing_nodes.keys() if n.startswith("combiner_")]
        inverter_nodes = [n for n in routing_nodes.keys() if n.startswith("inverter_")]
        
        if not combiner_nodes or not inverter_nodes:
            return routes  # Direct string-to-inverter system
        
        # Route each combiner output to inverter input
        for i, combiner_node in enumerate(combiner_nodes):
            inverter_node = inverter_nodes[0]  # Assume single inverter for now
            
            # Calculate combined current from all strings in combiner
            summary = system_design.get("summary", {})
            strings_per_combiner = min(6, summary.get("num_strings", 1))
            
            module_component = self.component_library.get_component(
                system_design["components"]["modules"]["component_id"]
            )
            string_current = module_component.electrical_specs.current_max or 10
            total_current = strings_per_combiner * string_current
            
            # Calculate distance and wire size
            distance = self._calculate_distance(
                routing_nodes[combiner_node].position,
                routing_nodes[inverter_node].position
            )
            
            wire_size = self._calculate_wire_size(total_current, distance, voltage_drop_percent=2.0)
            
            # DC main route
            route = RouteSegment(
                route_id=f"dc_main_{i+1}",
                route_type=RouteType.DC_MAIN,
                source_component=combiner_node,
                target_component=inverter_node,
                source_port="dc_out_pos",
                target_port="dc_in_pos",
                voltage_type="dc",
                max_voltage=summary.get("modules_per_string", 10) * (module_component.electrical_specs.voltage_dc_max or 48),
                max_current=total_current,
                wire_type="THWN-2",
                wire_size=wire_size,
                conduit_type="EMT",
                conduit_size=self._calculate_conduit_size(wire_size, 2),  # 2 conductors
                nec_article="690.31",
                installation_method="conduit",
                protection_devices=["dc_disconnect_60a"]  # DC disconnect required
            )
            
            routes.append(route)
        
        return routes
    
    def _route_ac_output_connections(self, routing_nodes: Dict[str, RoutingNode],
                                   system_design: Dict) -> List[RouteSegment]:
        """Route AC output connections"""
        
        routes = []
        
        inverter_nodes = [n for n in routing_nodes.keys() if n.startswith("inverter_")]
        
        for inverter_node in inverter_nodes:
            # Route to production meter (if present)
            meter_node = "production_meter"
            if meter_node in routing_nodes:
                
                inverter_info = system_design["components"]["inverters"]
                inverter_component = self.component_library.get_component(inverter_info["component_id"])
                
                ac_current = (inverter_component.electrical_specs.power_max or 10000) / (480 * math.sqrt(3))  # 3-phase power
                
                distance = self._calculate_distance(
                    routing_nodes[inverter_node].position,
                    routing_nodes[meter_node].position
                )
                
                wire_size = self._calculate_wire_size(ac_current, distance, voltage_drop_percent=3.0)
                
                route = RouteSegment(
                    route_id=f"ac_inverter_to_meter",
                    route_type=RouteType.AC_INVERTER,
                    source_component=inverter_node,
                    target_component=meter_node,
                    source_port="ac_out_l1",
                    target_port="ac_in_l1",
                    voltage_type="ac",
                    max_voltage=480,
                    max_current=ac_current,
                    wire_type="THWN-2",
                    wire_size=wire_size,
                    conduit_type="EMT",
                    conduit_size=self._calculate_conduit_size(wire_size, 4),  # 3 phase + neutral
                    nec_article="690.64",
                    installation_method="conduit",
                    protection_devices=["ac_breaker_40a_3p"]
                )
                
                routes.append(route)
        
        return routes
    
    def _generate_grounding_routes(self, routing_nodes: Dict[str, RoutingNode]) -> List[RouteSegment]:
        """Generate equipment grounding routes"""
        
        routes = []
        
        # All components need grounding connection
        grounding_nodes = list(routing_nodes.keys())
        
        for i, node_id in enumerate(grounding_nodes):
            if i == 0:
                continue  # Skip first node (grounding electrode)
            
            route = RouteSegment(
                route_id=f"ground_{i}",
                route_type=RouteType.GROUND,
                source_component=grounding_nodes[0],  # Main grounding point
                target_component=node_id,
                source_port="ground",
                target_port="ground",
                voltage_type="ground",
                max_voltage=0,
                max_current=0,
                wire_type="Bare Copper",
                wire_size="8 AWG",  # Standard equipment grounding
                nec_article="690.43",
                installation_method="conduit"
            )
            
            routes.append(route)
        
        return routes
    
    def _generate_data_routes(self, routing_nodes: Dict[str, RoutingNode]) -> List[RouteSegment]:
        """Generate monitoring and data communication routes"""
        
        routes = []
        
        # Find components with data ports
        data_nodes = []
        for node_id, node in routing_nodes.items():
            component = self.component_library.get_component(node.component_id)
            if component and any(port.type == "data" for port in component.ports):
                data_nodes.append(node_id)
        
        # Create data network (star topology from main monitoring point)
        if len(data_nodes) > 1:
            main_node = data_nodes[0]  # Assume first is main monitoring point
            
            for node_id in data_nodes[1:]:
                route = RouteSegment(
                    route_id=f"data_{node_id}",
                    route_type=RouteType.DATA,
                    source_component=main_node,
                    target_component=node_id,
                    source_port="data",
                    target_port="data",
                    voltage_type="data",
                    max_voltage=48,  # Low voltage data
                    max_current=1,
                    wire_type="Cat6",
                    wire_size="22 AWG",
                    nec_article="690.71",
                    installation_method="conduit"
                )
                
                routes.append(route)
        
        return routes
    
    def _optimize_routing_paths(self, routes: List[RouteSegment], 
                              routing_nodes: Dict[str, RoutingNode]) -> List[RouteSegment]:
        """Optimize routing paths for efficiency and code compliance"""
        
        # Group routes by conduit runs
        conduit_groups = {}
        
        for route in routes:
            # Create conduit group key based on approximate path
            source_pos = routing_nodes[route.source_component].position
            target_pos = routing_nodes[route.target_component].position
            
            # Simple path grouping - could be enhanced with actual pathfinding
            path_key = f"{int(source_pos[0]/100)}_{int(source_pos[1]/100)}_to_{int(target_pos[0]/100)}_{int(target_pos[1]/100)}"
            
            if path_key not in conduit_groups:
                conduit_groups[path_key] = []
            
            conduit_groups[path_key].append(route)
        
        # Optimize conduit sizing for grouped routes
        for group_routes in conduit_groups.values():
            if len(group_routes) > 1:
                # Calculate combined conduit size
                total_conductors = sum(2 if r.voltage_type == "dc" else 4 for r in group_routes)  # DC=2, AC=4 conductors
                max_wire_size = max(self._wire_size_to_area(r.wire_size) for r in group_routes)
                
                combined_conduit_size = self._calculate_conduit_size_for_multiple_circuits(
                    total_conductors, max_wire_size
                )
                
                # Update all routes in group with optimized conduit
                for route in group_routes:
                    route.conduit_size = combined_conduit_size
        
        return routes
    
    def _add_protection_device_routing(self, routes: List[RouteSegment], 
                                     system_design: Dict) -> List[RouteSegment]:
        """Add routing for protection devices"""
        
        enhanced_routes = []
        
        for route in routes:
            enhanced_routes.append(route)
            
            # Add disconnect switches on DC main circuits
            if route.route_type == RouteType.DC_MAIN:
                # Insert DC disconnect in the route
                disconnect_route = RouteSegment(
                    route_id=f"{route.route_id}_disconnect",
                    route_type=RouteType.DC_MAIN,
                    source_component=route.source_component,
                    target_component="dc_disconnect_60a",
                    source_port=route.source_port,
                    target_port="line_pos",
                    voltage_type=route.voltage_type,
                    max_voltage=route.max_voltage,
                    max_current=route.max_current,
                    wire_type=route.wire_type,
                    wire_size=route.wire_size,
                    nec_article="690.13",
                    installation_method=route.installation_method
                )
                
                enhanced_routes.append(disconnect_route)
                
                # Modify original route to come from disconnect
                route.source_component = "dc_disconnect_60a"
                route.source_port = "load_pos"
            
            # Add AC breakers on AC circuits
            if route.route_type == RouteType.AC_INVERTER:
                # Insert AC breaker
                breaker_route = RouteSegment(
                    route_id=f"{route.route_id}_breaker",
                    route_type=RouteType.AC_MAIN,
                    source_component=route.target_component,
                    target_component="ac_breaker_40a_3p",
                    source_port=route.target_port,
                    target_port="load_l1",
                    voltage_type=route.voltage_type,
                    max_voltage=route.max_voltage,
                    max_current=route.max_current,
                    wire_type=route.wire_type,
                    wire_size=route.wire_size,
                    nec_article="690.64",
                    installation_method=route.installation_method
                )
                
                enhanced_routes.append(breaker_route)
        
        return enhanced_routes
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate distance between two positions"""
        return math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
    
    def _calculate_wire_size(self, current: float, distance: float, 
                           voltage_drop_percent: float = 3.0) -> str:
        """Calculate appropriate wire size based on current and voltage drop"""
        
        # NEC Table 310.15(B)(16) current carrying capacity
        # Simplified - in production, use full derating factors
        wire_sizes = {
            "14 AWG": 20,
            "12 AWG": 25,
            "10 AWG": 35,
            "8 AWG": 50,
            "6 AWG": 65,
            "4 AWG": 85,
            "2 AWG": 115,
            "1/0 AWG": 150,
            "2/0 AWG": 175,
            "3/0 AWG": 200,
            "4/0 AWG": 230
        }
        
        # Find minimum wire size for current capacity
        min_current_capacity = current * 1.25  # 125% rule
        suitable_wires = [(size, capacity) for size, capacity in wire_sizes.items() 
                         if capacity >= min_current_capacity]
        
        if not suitable_wires:
            return "4/0 AWG"  # Largest standard size
        
        # Check voltage drop
        # Simplified calculation - use proper resistance values in production
        for wire_size, capacity in suitable_wires:
            # Approximate resistance in ohms per 1000 ft
            resistance_per_1000ft = {"14 AWG": 2.525, "12 AWG": 1.588, "10 AWG": 0.999,
                                   "8 AWG": 0.628, "6 AWG": 0.395, "4 AWG": 0.249}.get(wire_size, 0.1)
            
            voltage_drop = (2 * current * distance * resistance_per_1000ft / 1000) / 480 * 100
            
            if voltage_drop <= voltage_drop_percent:
                return wire_size
        
        return suitable_wires[-1][0]  # Return largest suitable wire
    
    def _wire_size_to_area(self, wire_size: str) -> float:
        """Convert wire size to cross-sectional area (for conduit calculations)"""
        # Simplified - use actual NEC Chapter 9 tables in production
        areas = {
            "14 AWG": 0.0097,
            "12 AWG": 0.0133,
            "10 AWG": 0.0211,
            "8 AWG": 0.0366,
            "6 AWG": 0.0507,
            "4 AWG": 0.0824
        }
        return areas.get(wire_size, 0.1)
    
    def _calculate_conduit_size(self, wire_size: str, num_conductors: int) -> str:
        """Calculate conduit size for given wires"""
        # Simplified - use NEC Chapter 9 fill calculations in production
        wire_area = self._wire_size_to_area(wire_size)
        total_area = wire_area * num_conductors
        
        # 40% fill factor for 3+ conductors
        required_conduit_area = total_area / 0.4
        
        conduit_sizes = {
            "1/2\"": 0.125,
            "3/4\"": 0.220,
            "1\"": 0.384,
            "1-1/4\"": 0.610,
            "1-1/2\"": 0.814,
            "2\"": 1.363
        }
        
        for size, area in conduit_sizes.items():
            if area >= required_conduit_area:
                return size
        
        return "2\""  # Largest standard size
    
    def _calculate_conduit_size_for_multiple_circuits(self, total_conductors: int, 
                                                    max_wire_area: float) -> str:
        """Calculate conduit size for multiple circuits"""
        # Conservative approach - assume all conductors are max size
        total_area = max_wire_area * total_conductors
        required_conduit_area = total_area / 0.4  # 40% fill
        
        conduit_sizes = {
            "1/2\"": 0.125,
            "3/4\"": 0.220,
            "1\"": 0.384,
            "1-1/4\"": 0.610,
            "1-1/2\"": 0.814,
            "2\"": 1.363,
            "2-1/2\"": 2.071,
            "3\"": 3.169
        }
        
        for size, area in conduit_sizes.items():
            if area >= required_conduit_area:
                return size
        
        return "3\""
    
    def _load_wire_sizing_table(self) -> Dict[str, Dict]:
        """Load wire sizing tables from NEC"""
        return {
            "ampacity": {
                "14 AWG": 20,
                "12 AWG": 25,
                "10 AWG": 35,
                "8 AWG": 50,
                "6 AWG": 65,
                "4 AWG": 85
            },
            "resistance": {  # Ohms per 1000 ft
                "14 AWG": 2.525,
                "12 AWG": 1.588,
                "10 AWG": 0.999,
                "8 AWG": 0.628,
                "6 AWG": 0.395,
                "4 AWG": 0.249
            }
        }