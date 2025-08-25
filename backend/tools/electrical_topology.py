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
    
    def create_dc_string_connections(self, panel_ids: List[str], target_mppt: Tuple[str, int]) -> List[ElectricalConnection]:
        """Create series connections for DC string (panel + to panel - to next panel +, etc.)."""
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
        
        # Connect string to inverter MPPT channel
        # First panel negative to inverter MPPT negative
        first_panel = panel_ids[0]
        mppt_neg_terminal = f"mppt{mppt_channel}_negative"
        
        connection = ElectricalConnection(
            source_component=first_panel,
            source_terminal="dc_negative",
            target_component=inverter_id,
            target_terminal=mppt_neg_terminal,
            connection_type="dc_string_to_inverter"
        )
        connections.append(connection)
        
        # Last panel positive to inverter MPPT positive  
        last_panel = panel_ids[-1]
        mppt_pos_terminal = f"mppt{mppt_channel}_positive"
        
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
        
        for i in range(len(ac_chain) - 1):
            source_comp = ac_chain[i]
            target_comp = ac_chain[i + 1]
            
            # Determine terminals based on component types
            if source_comp == inverter_id:
                source_terminals = ["ac_l1", "ac_l2", "ac_neutral"]
                target_terminals = ["line_in", "line_in", "line_in"]  # Protection/disconnect line side
            else:
                source_terminals = ["load_out", "load_out", "load_out"]  # Load side
                target_terminals = ["line_in", "line_in", "line_in"]     # Line side of next device
            
            # Create connections for each AC conductor (L1, L2, N)
            for j, (source_term, target_term) in enumerate(zip(source_terminals, target_terminals)):
                phase = ["L1", "L2", "N"][j]
                connection = ElectricalConnection(
                    source_component=source_comp,
                    source_terminal=source_term,
                    target_component=target_comp,  
                    target_terminal=target_term,
                    connection_type=f"ac_circuit_{phase.lower()}"
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
        
        # Separate components by type
        panels = [cid for cid, cdata in components.items() if cdata.get("type") == "panel"]
        inverters = [cid for cid, cdata in components.items() if cdata.get("type") == "inverter"]  
        protections = [cid for cid, cdata in components.items() if cdata.get("type") == "protection"]
        disconnects = [cid for cid, cdata in components.items() if cdata.get("type") == "disconnect"]
        
        logger.info(f"Generating connections: {len(panels)} panels, {len(inverters)} inverters, {len(protections)} protection, {len(disconnects)} disconnects")
        
        if not panels or not inverters:
            logger.warning("Cannot generate connections: missing panels or inverters")
            return all_connections
        
        # Create DC string connections
        primary_inverter = inverters[0]  # Use first inverter for now
        inverter_data = components[primary_inverter]
        mppts = inverter_data.get("attrs", {}).get("mppts", 2)
        
        # Group panels into strings (simple: divide panels evenly across MPPT channels)  
        panels_per_string = len(panels) // mppts
        remainder = len(panels) % mppts
        
        panel_idx = 0
        for mppt_channel in range(1, mppts + 1):
            string_size = panels_per_string + (1 if mppt_channel <= remainder else 0)
            string_panels = panels[panel_idx:panel_idx + string_size]
            
            if string_panels:
                string_connections = self.create_dc_string_connections(string_panels, (primary_inverter, mppt_channel))
                all_connections.extend(string_connections)
                
            panel_idx += string_size
        
        # Create AC circuit connections
        ac_protections = [pid for pid in protections if components[pid].get("attrs", {}).get("type", "").startswith("ac_")]
        ac_disconnects = [did for did in disconnects if components[did].get("attrs", {}).get("type", "").startswith("ac_")]
        
        if inverters:
            ac_connections = self.create_ac_circuit_connections(primary_inverter, ac_protections, ac_disconnects)
            all_connections.extend(ac_connections)
        
        logger.info(f"Generated {len(all_connections)} electrical connections")
        return all_connections


def create_electrical_connections(components: Dict[str, Dict[str, Any]]) -> List[ElectricalConnection]:
    """Main entry point for generating electrical connections."""
    engine = ElectricalTopologyEngine()
    return engine.generate_system_connections(components)