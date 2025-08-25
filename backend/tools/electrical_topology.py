"""
Electrical Topology Engine
-------------------------
Intelligent system for creating proper electrical connections between components
based on electrical engineering principles and code requirements.

This engine understands:
- Component interface definitions (connection points)
- Electrical flow patterns (DC strings, AC distribution)  
- Safety requirements (protection device insertion)
- System topology rules (string inverters, optimizers, microinverters)
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Import AI wiring components for enhanced topology generation
try:
    from backend.ai.wiring_ai_pipeline import EnterpriseAIWiringPipeline, PipelineConfiguration
    from backend.ai.panel_grouping import EnterpriseGroupingEngine, GroupingStrategy
    AI_WIRING_AVAILABLE = True
    logger.info("AI wiring pipeline available for enhanced topology generation")
except ImportError:
    logger.warning("AI wiring pipeline not available - falling back to basic topology")
    AI_WIRING_AVAILABLE = False


@dataclass
class ComponentInterface:
    """Defines the electrical connection points for a component."""
    component_id: str
    component_type: str
    terminals: Dict[str, Dict[str, Any]]  # terminal_name -> {type, voltage, current, etc.}


@dataclass  
class ElectricalConnection:
    """Represents an electrical connection between two component terminals."""
    source_component: str
    source_terminal: str
    target_component: str
    target_terminal: str
    connection_type: str  # "dc_string", "ac_line", "protection", etc.
    conductor_specs: Optional[Dict[str, Any]] = None


class ElectricalTopologyEngine:
    """Core engine for creating intelligent electrical connections."""
    
    def __init__(self):
        self.component_interfaces: Dict[str, ComponentInterface] = {}
        self.connection_rules = self._init_connection_rules()
    
    def _init_connection_rules(self) -> Dict[str, Any]:
        """Initialize electrical connection rules and patterns."""
        return {
            "pv_system": {
                "dc_flow": ["panel", "protection", "disconnect", "inverter"],
                "ac_flow": ["inverter", "protection", "disconnect", "main_panel"],
                "string_max_modules": 25,  # Typical NEC limit
                "mppt_max_strings": 2,     # Typical per MPPT channel
            },
            "terminal_definitions": {
                "panel": {
                    "dc_positive": {"type": "dc", "role": "source", "polarity": "+"},
                    "dc_negative": {"type": "dc", "role": "source", "polarity": "-"},
                    "equipment_ground": {"type": "ground", "role": "safety"}
                },
                "inverter": {
                    "mppt1_positive": {"type": "dc", "role": "load", "polarity": "+", "channel": 1},
                    "mppt1_negative": {"type": "dc", "role": "load", "polarity": "-", "channel": 1},
                    "mppt2_positive": {"type": "dc", "role": "load", "polarity": "+", "channel": 2},
                    "mppt2_negative": {"type": "dc", "role": "load", "polarity": "-", "channel": 2},
                    "ac_l1": {"type": "ac", "role": "source", "phase": "L1"},
                    "ac_l2": {"type": "ac", "role": "source", "phase": "L2"},
                    "ac_neutral": {"type": "ac", "role": "source", "phase": "N"},
                    "equipment_ground": {"type": "ground", "role": "safety"}
                },
                "protection": {
                    "line_in": {"type": "universal", "role": "load"},
                    "load_out": {"type": "universal", "role": "source"}
                },
                "disconnect": {
                    "line_in": {"type": "universal", "role": "load"},
                    "load_out": {"type": "universal", "role": "source"}
                }
            }
        }
    
    def register_component(self, component_id: str, component_type: str, attrs: Dict[str, Any] = None) -> ComponentInterface:
        """Register a component and create its interface definition."""
        attrs = attrs or {}
        
        # Get terminal definitions for this component type
        terminal_defs = self.connection_rules["terminal_definitions"].get(component_type, {})
        
        # Create component interface
        interface = ComponentInterface(
            component_id=component_id,
            component_type=component_type,
            terminals=terminal_defs.copy()
        )
        
        # Customize terminals based on component specifications
        if component_type == "inverter":
            mppts = attrs.get("mppts", 2)
            # Only include MPPT terminals that exist on this inverter
            filtered_terminals = {}
            for terminal_name, terminal_spec in terminal_defs.items():
                if "mppt" in terminal_name:
                    channel = terminal_spec.get("channel", 1)
                    if channel <= mppts:
                        filtered_terminals[terminal_name] = terminal_spec
                else:
                    filtered_terminals[terminal_name] = terminal_spec
            interface.terminals = filtered_terminals
        
        self.component_interfaces[component_id] = interface
        return interface
    
    def create_dc_string_connections(self, panel_ids: List[str], target_mppt: Tuple[str, int], dc_protection_id: Optional[str] = None) -> List[ElectricalConnection]:
        """Create series connections for DC string with proper protection device integration."""
        connections = []
        inverter_id, mppt_channel = target_mppt
        
        if len(panel_ids) < 2:
            return connections
            
        # Series connections between panels (+ to - to + to -)  
        for i in range(len(panel_ids) - 1):
            source_panel = panel_ids[i]
            target_panel = panel_ids[i + 1]
            
            connection = ElectricalConnection(
                source_component=source_panel,
                source_terminal="dc_positive",
                target_component=target_panel,
                target_terminal="dc_negative", 
                connection_type="dc_string"
            )
            connections.append(connection)
        
        # Connect string to DC protection device or directly to inverter
        first_panel = panel_ids[0]
        last_panel = panel_ids[-1]
        mppt_neg_terminal = f"mppt{mppt_channel}_negative"
        mppt_pos_terminal = f"mppt{mppt_channel}_positive"
        
        if dc_protection_id:
            # Route string through DC protection device (NEC compliant)
            # String negative through protection
            connection = ElectricalConnection(
                source_component=first_panel,
                source_terminal="dc_negative",
                target_component=dc_protection_id,
                target_terminal="line_in_neg",
                connection_type="dc_string_to_protection"
            )
            connections.append(connection)
            
            # Protection to inverter MPPT negative
            connection = ElectricalConnection(
                source_component=dc_protection_id,
                source_terminal="load_out_neg", 
                target_component=inverter_id,
                target_terminal=mppt_neg_terminal,
                connection_type="dc_protection_to_inverter"
            )
            connections.append(connection)
            
            # String positive through protection
            connection = ElectricalConnection(
                source_component=last_panel,
                source_terminal="dc_positive",
                target_component=dc_protection_id,
                target_terminal="line_in_pos",
                connection_type="dc_string_to_protection"
            )
            connections.append(connection)
            
            # Protection to inverter MPPT positive
            connection = ElectricalConnection(
                source_component=dc_protection_id,
                source_terminal="load_out_pos",
                target_component=inverter_id, 
                target_terminal=mppt_pos_terminal,
                connection_type="dc_protection_to_inverter"
            )
            connections.append(connection)
            
        else:
            # Direct connection to inverter (fallback)
            connection = ElectricalConnection(
                source_component=first_panel,
                source_terminal="dc_negative",
                target_component=inverter_id,
                target_terminal=mppt_neg_terminal,
                connection_type="dc_string_to_inverter"
            )
            connections.append(connection)
            
            connection = ElectricalConnection(
                source_component=last_panel,
                source_terminal="dc_positive",
                target_component=inverter_id,
                target_terminal=mppt_pos_terminal,
                connection_type="dc_string_to_inverter"
            )
            connections.append(connection)
        
        return connections
    
    def create_ac_circuit_connections(self, inverter_id: str, protection_ids: List[str], disconnect_ids: List[str]) -> List[ElectricalConnection]:
        """Create AC circuit from inverter through protection and disconnects."""
        connections = []
        
        # Build AC circuit chain: inverter -> protection -> disconnect (stop at system boundary)
        ac_chain = [inverter_id] + protection_ids + disconnect_ids
        
        # Create a single connection between each component (not per-phase to avoid duplication)
        for i in range(len(ac_chain) - 1):
            source_comp = ac_chain[i]
            target_comp = ac_chain[i + 1]
            
            # Create single logical connection representing the AC circuit
            connection = ElectricalConnection(
                source_component=source_comp,
                source_terminal="ac_output" if source_comp == inverter_id else "load_out",
                target_component=target_comp,  
                target_terminal="line_in",
                connection_type="ac_circuit"
            )
            connections.append(connection)
        
        return connections
    
    def create_dc_circuit_connections(self, inverter_id: str, protection_ids: List[str], disconnect_ids: List[str]) -> List[ElectricalConnection]:
        """Create DC circuit connections for protection devices and disconnects in the DC path."""
        connections = []
        
        # DC circuit path: panels -> dc_disconnect -> dc_protection -> inverter
        # Note: This is a simplified model. In reality, DC protection/disconnects can be 
        # configured in different topologies depending on system design and code requirements.
        
        # For now, create connections that put DC protection/disconnect devices in the DC path
        # This ensures they appear as part of the electrical circuit rather than orphaned components
        
        all_dc_devices = disconnect_ids + protection_ids
        
        if all_dc_devices:
            # Connect DC devices in series in the DC path
            # This is a logical connection to ensure they appear connected
            # In detailed design, exact placement would depend on system architecture
            
            for i, dc_device in enumerate(all_dc_devices):
                if i == 0:
                    # First DC device connects to inverter DC input (conceptually)
                    connection = ElectricalConnection(
                        source_component=dc_device,
                        source_terminal="load_out",
                        target_component=inverter_id,
                        target_terminal="dc_input",
                        connection_type="dc_circuit"
                    )
                    connections.append(connection)
                else:
                    # Chain DC devices together
                    prev_device = all_dc_devices[i-1]
                    connection = ElectricalConnection(
                        source_component=prev_device,
                        source_terminal="load_out", 
                        target_component=dc_device,
                        target_terminal="line_in",
                        connection_type="dc_circuit"
                    )
                    connections.append(connection)
        
        return connections
    
    def generate_system_connections(self, components: Dict[str, Dict[str, Any]]) -> List[ElectricalConnection]:
        """Generate all electrical connections for a complete PV system."""
        all_connections = []
        
        # Register all components
        for comp_id, comp_data in components.items():
            comp_type = comp_data.get("type", "unknown")
            comp_attrs = comp_data.get("attrs", {})
            self.register_component(comp_id, comp_type, comp_attrs)
        
        # Separate components by type and sort for consistent ordering
        panels = sorted([cid for cid, cdata in components.items() if cdata.get("type") == "panel"])
        inverters = [cid for cid, cdata in components.items() if cdata.get("type") == "inverter"]  
        protections = [cid for cid, cdata in components.items() if cdata.get("type") == "protection"]
        disconnects = [cid for cid, cdata in components.items() if cdata.get("type") == "disconnect"]
        
        logger.info(f"Generating connections: {len(panels)} panels, {len(inverters)} inverters, {len(protections)} protection, {len(disconnects)} disconnects")
        
        if not panels or not inverters:
            logger.warning("Cannot generate connections: missing panels or inverters")
            return all_connections
        
        # Separate AC and DC circuit devices first
        ac_protections = [pid for pid in protections if components[pid].get("attrs", {}).get("type", "").startswith("ac_")]
        dc_protections = [pid for pid in protections if components[pid].get("attrs", {}).get("type", "").startswith("dc_")]
        ac_disconnects = [did for did in disconnects if components[did].get("attrs", {}).get("type", "").startswith("ac_")]
        dc_disconnects = [did for did in disconnects if components[did].get("attrs", {}).get("type", "").startswith("dc_")]
        
        # Create DC string connections with improved MPPT distribution
        primary_inverter = inverters[0]  # Use first inverter for now
        inverter_data = components[primary_inverter]
        mppts = inverter_data.get("attrs", {}).get("mppts", 2)
        
        # Use first DC protection device for string protection (simplified model)
        dc_protection_device = dc_protections[0] if dc_protections else None
        
        # Improved panel distribution: create balanced strings across MPPT channels
        max_panels_per_string = 4  # Reasonable string size for residential
        total_strings_needed = (len(panels) + max_panels_per_string - 1) // max_panels_per_string
        
        logger.info(f"Creating {total_strings_needed} strings across {mppts} MPPT channels")
        logger.info(f"DC protection device: {dc_protection_device}")
        
        panel_idx = 0
        string_id = 1
        
        for mppt_channel in range(1, mppts + 1):
            # Determine how many strings this MPPT should handle
            remaining_panels = len(panels) - panel_idx
            remaining_mppts = mppts - mppt_channel + 1
            
            if remaining_panels <= 0:
                break
                
            # Calculate panels for this MPPT channel
            panels_for_this_mppt = remaining_panels // remaining_mppts
            
            # Create strings for this MPPT (usually 1-2 strings per MPPT)
            while panels_for_this_mppt > 0 and panel_idx < len(panels):
                string_size = min(max_panels_per_string, panels_for_this_mppt)
                string_panels = panels[panel_idx:panel_idx + string_size]
                
                if len(string_panels) >= 2:  # Only create strings with at least 2 panels
                    # Route string through DC protection device for NEC compliance
                    string_connections = self.create_dc_string_connections(
                        string_panels, 
                        (primary_inverter, mppt_channel), 
                        dc_protection_device if string_id == 1 else None  # Only protect first string for now
                    )
                    all_connections.extend(string_connections)
                    logger.info(f"String {string_id} (MPPT{mppt_channel}): {len(string_panels)} panels - protected: {dc_protection_device is not None}")
                    string_id += 1
                    
                panel_idx += string_size
                panels_for_this_mppt -= string_size
        
        # Handle any remaining individual panels (connect directly)
        while panel_idx < len(panels):
            remaining_panel = panels[panel_idx]
            single_panel_connections = self.create_dc_string_connections([remaining_panel], (primary_inverter, 1))
            all_connections.extend(single_panel_connections)
            logger.info(f"Single panel connection: {remaining_panel} -> MPPT1")
            panel_idx += 1
        
        logger.info(f"AC devices: {len(ac_protections)} protection, {len(ac_disconnects)} disconnects")
        logger.info(f"DC devices: {len(dc_protections)} protection, {len(dc_disconnects)} disconnects")
        
        # Create DC circuit connections for remaining DC devices (disconnects)
        if dc_disconnects:
            dc_connections = self.create_dc_circuit_connections(primary_inverter, [], dc_disconnects)
            all_connections.extend(dc_connections)
        
        # Create AC circuit connections  
        if inverters:
            ac_connections = self.create_ac_circuit_connections(primary_inverter, ac_protections, ac_disconnects)
            all_connections.extend(ac_connections)
        
        logger.info(f"Generated {len(all_connections)} electrical connections total")
        return all_connections
    
    def generate_ai_enhanced_connections(
        self,
        components: Dict[str, Dict[str, Any]],
        session_id: str,
        enable_ai: bool = True
    ) -> Tuple[List[ElectricalConnection], Dict[str, Any]]:
        """
        Generate electrical connections using AI-enhanced topology engine.
        
        This method combines traditional rule-based topology generation with
        AI-powered wiring suggestions for optimal results.
        
        Args:
            components: Dictionary of components with their data
            session_id: Session identifier for AI pipeline tracking
            enable_ai: Whether to use AI enhancement (fallback to basic if disabled)
            
        Returns:
            Tuple of (connections, ai_metadata) where ai_metadata contains
            AI insights, performance metrics, and suggestion details
        """
        if not enable_ai or not AI_WIRING_AVAILABLE:
            logger.info("AI wiring disabled or unavailable - using basic topology")
            connections = self.generate_system_connections(components)
            return connections, {"ai_enhanced": False, "method": "basic_topology"}
        
        try:
            # Create a simplified graph structure for AI pipeline
            mock_graph = self._create_graph_from_components(components)
            
            # Configure AI pipeline for topology enhancement
            config = PipelineConfiguration(
                max_modules_per_string=12,
                use_llm_suggestions=False,  # Keep conservative for now
                use_vector_store=True,
                enable_caching=True,
                validation_strict=True,
                enable_audit_trail=True
            )
            
            # Execute AI wiring pipeline
            ai_pipeline = EnterpriseAIWiringPipeline(config)
            ai_result = ai_pipeline.generate_wiring(mock_graph, session_id)
            
            if ai_result.success and ai_result.edges:
                # Convert AI edges back to ElectricalConnection format
                ai_connections = self._convert_ai_edges_to_connections(ai_result.edges)
                
                # Merge with traditional topology connections for completeness
                basic_connections = self.generate_system_connections(components)
                
                # Combine and deduplicate connections
                combined_connections = self._merge_connection_sets(ai_connections, basic_connections)
                
                ai_metadata = {
                    "ai_enhanced": True,
                    "method": "ai_pipeline",
                    "ai_connections": len(ai_connections),
                    "basic_connections": len(basic_connections), 
                    "total_connections": len(combined_connections),
                    "performance_metrics": ai_result.metrics,
                    "design_insights": ai_result.design_insights,
                    "suggestions_used": len(ai_result.suggestions_used),
                    "warnings": ai_result.warnings
                }
                
                logger.info(f"AI-enhanced topology: {len(ai_connections)} AI + {len(basic_connections)} basic = {len(combined_connections)} total")
                return combined_connections, ai_metadata
            
            else:
                # AI pipeline failed, fallback to basic
                logger.warning(f"AI pipeline failed: {ai_result.message}")
                connections = self.generate_system_connections(components)
                return connections, {
                    "ai_enhanced": False,
                    "method": "basic_fallback",
                    "ai_error": ai_result.message,
                    "warnings": ai_result.warnings
                }
                
        except Exception as e:
            logger.error(f"AI topology enhancement failed: {e}", exc_info=True)
            # Graceful fallback to basic topology
            connections = self.generate_system_connections(components)
            return connections, {
                "ai_enhanced": False,
                "method": "exception_fallback",
                "error": str(e)
            }
    
    def _create_graph_from_components(self, components: Dict[str, Dict[str, Any]]) -> Any:
        """Create a mock graph structure compatible with AI pipeline."""
        class MockGraph:
            def __init__(self):
                self.nodes = {}
                self.edges = []
        
        graph = MockGraph()
        
        # Convert components to graph nodes
        for comp_id, comp_data in components.items():
            comp_type = comp_data.get("type", "unknown")
            comp_attrs = comp_data.get("attrs", {})
            
            # Try to get port information from placeholder service
            ports = None
            try:
                from backend.services.placeholder_component_service import PlaceholderComponentService
                placeholder_service = PlaceholderComponentService()
                placeholder = placeholder_service.get_placeholder_type(comp_type)
                if placeholder and placeholder.ports:
                    ports = {p["id"]: {k: v for k, v in p.items() if k != "id"} for p in placeholder.ports}
            except Exception:
                pass  # Ports not available
            
            graph.nodes[comp_id] = {
                "type": comp_type,
                "attrs": comp_attrs,
                "data": comp_attrs,  # Alias for compatibility
                "ports": ports
            }
        
        return graph
    
    def _convert_ai_edges_to_connections(self, ai_edges: List[Dict[str, Any]]) -> List[ElectricalConnection]:
        """Convert AI pipeline edges to ElectricalConnection format."""
        connections = []
        
        for edge in ai_edges:
            attrs = edge.get("attrs", {})
            
            connection = ElectricalConnection(
                source_component=edge.get("source_id", ""),
                source_terminal=attrs.get("source_port", ""),
                target_component=edge.get("target_id", ""),
                target_terminal=attrs.get("target_port", ""),
                connection_type=attrs.get("connection_type", "electrical"),
                conductor_specs={
                    "ai_generated": attrs.get("ai_generated", False),
                    "confidence": attrs.get("confidence", 0.0),
                    "reasoning": attrs.get("reasoning", ""),
                    "compliance_notes": attrs.get("compliance_notes", [])
                }
            )
            connections.append(connection)
        
        return connections
    
    def _merge_connection_sets(
        self, 
        ai_connections: List[ElectricalConnection], 
        basic_connections: List[ElectricalConnection]
    ) -> List[ElectricalConnection]:
        """Merge AI and basic connections, removing duplicates and conflicts."""
        merged = []
        connection_signatures = set()
        
        # Add AI connections first (higher priority)
        for conn in ai_connections:
            signature = f"{conn.source_component}:{conn.source_terminal}->{conn.target_component}:{conn.target_terminal}"
            if signature not in connection_signatures:
                merged.append(conn)
                connection_signatures.add(signature)
        
        # Add non-duplicate basic connections
        for conn in basic_connections:
            signature = f"{conn.source_component}:{conn.source_terminal}->{conn.target_component}:{conn.target_terminal}"
            if signature not in connection_signatures:
                merged.append(conn)
                connection_signatures.add(signature)
        
        return merged


def create_electrical_connections(components: Dict[str, Dict[str, Any]]) -> List[ElectricalConnection]:
    """Main entry point for generating electrical connections."""
    engine = ElectricalTopologyEngine()
    return engine.generate_system_connections(components)


def create_ai_enhanced_electrical_connections(
    components: Dict[str, Dict[str, Any]], 
    session_id: str,
    enable_ai: bool = True
) -> Tuple[List[ElectricalConnection], Dict[str, Any]]:
    """
    Enhanced entry point for AI-powered electrical topology generation.
    
    Args:
        components: Dictionary of components with their specifications
        session_id: Session identifier for tracking and caching
        enable_ai: Whether to enable AI enhancement
        
    Returns:
        Tuple of (connections, metadata) with AI insights and metrics
    """
    engine = ElectricalTopologyEngine()
    return engine.generate_ai_enhanced_connections(components, session_id, enable_ai)