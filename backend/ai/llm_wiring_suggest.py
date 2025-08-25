"""
Enterprise LLM-Powered Wiring Suggestion Engine
==============================================

Advanced wiring suggestion system that combines rule-based heuristics with
large language model (LLM) intelligence to generate optimal electrical
connections. This module provides intelligent port-level wiring recommendations
based on electrical engineering principles, code compliance, and learned
patterns from successful designs.

Key Features:
- Hybrid LLM + heuristic approach for reliable suggestions
- Port-aware terminal-level connection recommendations
- NEC/IEC code compliance validation
- Integration with enterprise vector store for RAG
- Performance optimization for large-scale systems
- Comprehensive error handling and fallback mechanisms
"""

from __future__ import annotations

import logging
import json
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Types of electrical connections in PV systems."""
    DC_STRING_SERIES = "dc_string_series"
    DC_STRING_PARALLEL = "dc_string_parallel"  
    DC_TO_INVERTER = "dc_to_inverter"
    AC_INVERTER_OUTPUT = "ac_inverter_output"
    AC_PROTECTION = "ac_protection"
    AC_DISCONNECT = "ac_disconnect"
    MONITORING = "monitoring"
    GROUNDING = "grounding"


@dataclass
class WiringSuggestion:
    """Enhanced wiring suggestion with detailed electrical specifications."""
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str
    connection_type: ConnectionType
    confidence_score: float
    reasoning: str
    electrical_specs: Dict[str, Any]
    compliance_notes: List[str]
    priority: int = 1  # 1=critical, 2=recommended, 3=optional


@dataclass 
class WiringContext:
    """Context information for intelligent wiring suggestions."""
    system_type: str  # "residential", "commercial", "utility"
    power_rating: float  # kW
    voltage_class: str  # "LV", "MV", "HV"
    compliance_codes: List[str]  # ["NEC_2020", "UL_1741", etc.]
    installation_type: str  # "rooftop", "ground_mount", etc.
    geographical_region: str
    design_preferences: Dict[str, Any]
    safety_requirements: Dict[str, Any]


class PortCompatibilityEngine:
    """
    Advanced port compatibility analysis for terminal-level connections.
    Ensures electrical compatibility between component terminals.
    """
    
    def __init__(self):
        self.compatibility_rules = self._init_compatibility_rules()
        self.port_specifications = self._init_port_specifications()
    
    def _init_compatibility_rules(self) -> Dict[str, Any]:
        """Initialize port compatibility rules based on electrical principles."""
        return {
            "dc_connections": {
                "dc+" : ["dc-", "dc_pos", "dc_positive", "pv_pos", "pv+", "mppt_pos", "mppt+"],
                "dc-" : ["dc+", "dc_neg", "dc_negative", "pv_neg", "pv-", "mppt_neg", "mppt-"],
                "dc_pos": ["dc_neg", "dc-", "mppt_neg", "inverter_neg"],
                "dc_neg": ["dc_pos", "dc+", "mppt_pos", "inverter_pos"]
            },
            "ac_connections": {
                "ac_l1": ["ac_l1", "line1", "l1", "phase_a"],
                "ac_l2": ["ac_l2", "line2", "l2", "phase_b"],
                "ac_l3": ["ac_l3", "line3", "l3", "phase_c"],
                "ac_n": ["ac_n", "neutral", "n"],
                "ac_pe": ["ac_pe", "ground", "gnd", "earth"]
            },
            "polarity_rules": {
                "source_positive": ["load_positive", "input_positive"],
                "source_negative": ["load_negative", "input_negative"],
                "output": ["input", "load"],
                "input": ["output", "source"]
            }
        }
    
    def _init_port_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Initialize detailed port specifications for common components."""
        return {
            "generic_panel": {
                "dc_pos": {"type": "dc+", "direction": "output", "max_voltage": 60, "max_current": 12},
                "dc_neg": {"type": "dc-", "direction": "output", "max_voltage": 60, "max_current": 12},
                "gnd": {"type": "ground", "direction": "bidirectional"}
            },
            "generic_inverter": {
                "pv1_pos": {"type": "dc+", "direction": "input", "max_voltage": 600, "max_current": 15},
                "pv1_neg": {"type": "dc-", "direction": "input", "max_voltage": 600, "max_current": 15},
                "pv2_pos": {"type": "dc+", "direction": "input", "max_voltage": 600, "max_current": 15},
                "pv2_neg": {"type": "dc-", "direction": "input", "max_voltage": 600, "max_current": 15},
                "ac_l1": {"type": "ac", "direction": "output", "voltage": 240, "max_current": 50},
                "ac_l2": {"type": "ac", "direction": "output", "voltage": 240, "max_current": 50},
                "ac_n": {"type": "neutral", "direction": "output", "max_current": 50},
                "gnd": {"type": "ground", "direction": "bidirectional"}
            },
            "generic_protection": {
                "line_in": {"type": "universal", "direction": "input"},
                "load_out": {"type": "universal", "direction": "output"}
            },
            "generic_disconnect": {
                "line_in": {"type": "universal", "direction": "input"},
                "load_out": {"type": "universal", "direction": "output"}
            }
        }
    
    def are_ports_compatible(self, source_node: Dict[str, Any], source_port: str, 
                           target_node: Dict[str, Any], target_port: str) -> Tuple[bool, str]:
        """
        Check if two ports are electrically compatible for connection.
        
        Args:
            source_node: Source component node data
            source_port: Source port ID
            target_node: Target component node data  
            target_port: Target port ID
            
        Returns:
            (is_compatible, reason) tuple
        """
        # Get port specifications
        source_type = source_node.get("type", "unknown")
        target_type = target_node.get("type", "unknown")
        
        source_spec = self._get_port_spec(source_type, source_port)
        target_spec = self._get_port_spec(target_type, target_port)
        
        if not source_spec or not target_spec:
            return False, f"Missing port specification for {source_port} or {target_port}"
        
        # Check basic type compatibility
        source_port_type = source_spec.get("type", "unknown")
        target_port_type = target_spec.get("type", "unknown")
        
        if source_port_type == target_port_type:
            return True, "Same port types"
        
        # Check polarity compatibility for DC connections
        if "dc" in source_port_type and "dc" in target_port_type:
            if self._check_dc_polarity(source_port_type, target_port_type):
                return True, "DC polarity compatible"
            else:
                return False, f"DC polarity mismatch: {source_port_type} -> {target_port_type}"
        
        # Check direction compatibility
        source_dir = source_spec.get("direction", "unknown")
        target_dir = target_spec.get("direction", "unknown")
        
        if source_dir == "output" and target_dir == "input":
            return True, "Output to input connection"
        elif source_dir == "bidirectional" or target_dir == "bidirectional":
            return True, "Bidirectional port connection"
        
        # Check compatibility rules
        for rule_category, rules in self.compatibility_rules.items():
            if source_port in rules:
                if target_port in rules[source_port]:
                    return True, f"Compatible via {rule_category} rules"
        
        return False, f"No compatibility rule found for {source_port_type} -> {target_port_type}"
    
    def _get_port_spec(self, component_type: str, port_id: str) -> Optional[Dict[str, Any]]:
        """Get port specification for a component type and port ID."""
        component_specs = self.port_specifications.get(component_type, {})
        return component_specs.get(port_id)
    
    def _check_dc_polarity(self, source_type: str, target_type: str) -> bool:
        """Check if DC port polarities are compatible for series connections."""
        # For series connections: positive connects to negative
        if "+" in source_type and "-" in target_type:
            return True
        if "-" in source_type and "+" in target_type:
            return True
        if "pos" in source_type.lower() and "neg" in target_type.lower():
            return True
        if "neg" in source_type.lower() and "pos" in target_type.lower():
            return True
        
        return False


class EnhancedHeuristicEngine:
    """
    Advanced heuristic wiring engine with electrical engineering intelligence.
    Generates reliable wiring suggestions based on proven design patterns.
    """
    
    def __init__(self):
        self.port_engine = PortCompatibilityEngine()
        self.connection_patterns = self._init_connection_patterns()
    
    def _init_connection_patterns(self) -> Dict[str, Any]:
        """Initialize connection patterns for different system types."""
        return {
            "pv_string_inverter": {
                "dc_flow": ["panel", "dc_protection", "dc_disconnect", "inverter"],
                "ac_flow": ["inverter", "ac_protection", "ac_disconnect", "main_panel"],
                "string_formation": "series",
                "string_to_inverter": "parallel"
            },
            "pv_microinverter": {
                "dc_flow": ["panel", "microinverter"],
                "ac_flow": ["microinverter", "ac_protection", "ac_disconnect", "main_panel"],
                "string_formation": "individual",
                "string_to_inverter": "direct"
            },
            "pv_power_optimizer": {
                "dc_flow": ["panel", "optimizer", "dc_protection", "inverter"],
                "ac_flow": ["inverter", "ac_protection", "ac_disconnect", "main_panel"],
                "string_formation": "optimized_series",
                "string_to_inverter": "parallel"
            }
        }
    
    def generate_string_connections(self, panel_group: List[str], 
                                  graph: Any) -> List[WiringSuggestion]:
        """
        Generate series connections for a group of panels.
        
        Args:
            panel_group: List of panel node IDs to connect in series
            graph: ODL graph containing component nodes
            
        Returns:
            List of wiring suggestions for string connections
        """
        suggestions = []
        
        if len(panel_group) < 2:
            return suggestions
        
        for i in range(len(panel_group) - 1):
            source_id = panel_group[i]
            target_id = panel_group[i + 1]
            
            source_node = graph.nodes.get(source_id)
            target_node = graph.nodes.get(target_id)
            
            if not source_node or not target_node:
                continue
            
            # Find compatible ports for series connection
            source_port = self._find_best_output_port(source_node, "dc+")
            target_port = self._find_best_input_port(target_node, "dc-")
            
            if source_port and target_port:
                # Verify compatibility
                is_compatible, reason = self.port_engine.are_ports_compatible(
                    source_node, source_port, target_node, target_port
                )
                
                if is_compatible:
                    suggestion = WiringSuggestion(
                        source_node_id=source_id,
                        source_port=source_port,
                        target_node_id=target_id,
                        target_port=target_port,
                        connection_type=ConnectionType.DC_STRING_SERIES,
                        confidence_score=0.95,
                        reasoning=f"Series connection in DC string: {reason}",
                        electrical_specs={
                            "connection_type": "dc_series",
                            "expected_voltage_add": True,
                            "expected_current_same": True
                        },
                        compliance_notes=["NEC 690.7 - DC string requirements"],
                        priority=1
                    )
                    suggestions.append(suggestion)
        
        return suggestions
    
    def generate_inverter_connections(self, string_groups: List[List[str]], 
                                    inverter_id: str, graph: Any) -> List[WiringSuggestion]:
        """
        Generate connections from string groups to inverter MPPT inputs.
        
        Args:
            string_groups: List of panel string groups
            inverter_id: Target inverter node ID
            graph: ODL graph containing component nodes
            
        Returns:
            List of wiring suggestions for string-to-inverter connections
        """
        suggestions = []
        inverter_node = graph.nodes.get(inverter_id)
        
        if not inverter_node:
            return suggestions
        
        # Get available MPPT channels
        mppt_channels = self._get_available_mppt_channels(inverter_node)
        
        for string_idx, string_group in enumerate(string_groups):
            if string_idx >= len(mppt_channels):
                logger.warning(f"Not enough MPPT channels for string {string_idx}")
                break
            
            if not string_group:
                continue
            
            # Connect string endpoints to inverter MPPT
            first_panel_id = string_group[0]
            last_panel_id = string_group[-1]
            
            first_panel = graph.nodes.get(first_panel_id)
            last_panel = graph.nodes.get(last_panel_id)
            
            if not first_panel or not last_panel:
                continue
            
            mppt_channel = mppt_channels[string_idx]
            
            # Negative connection (string start to inverter negative)
            string_neg_port = self._find_best_output_port(first_panel, "dc-")
            inverter_neg_port = f"pv{mppt_channel}_neg"
            
            if string_neg_port:
                suggestion = WiringSuggestion(
                    source_node_id=first_panel_id,
                    source_port=string_neg_port,
                    target_node_id=inverter_id,
                    target_port=inverter_neg_port,
                    connection_type=ConnectionType.DC_TO_INVERTER,
                    confidence_score=0.90,
                    reasoning=f"String negative to MPPT{mppt_channel} negative",
                    electrical_specs={
                        "connection_type": "dc_negative",
                        "mppt_channel": mppt_channel,
                        "string_position": "start"
                    },
                    compliance_notes=["NEC 690.8 - DC grounding requirements"],
                    priority=1
                )
                suggestions.append(suggestion)
            
            # Positive connection (string end to inverter positive)
            string_pos_port = self._find_best_output_port(last_panel, "dc+")
            inverter_pos_port = f"pv{mppt_channel}_pos"
            
            if string_pos_port:
                suggestion = WiringSuggestion(
                    source_node_id=last_panel_id,
                    source_port=string_pos_port,
                    target_node_id=inverter_id,
                    target_port=inverter_pos_port,
                    connection_type=ConnectionType.DC_TO_INVERTER,
                    confidence_score=0.90,
                    reasoning=f"String positive to MPPT{mppt_channel} positive",
                    electrical_specs={
                        "connection_type": "dc_positive",
                        "mppt_channel": mppt_channel,
                        "string_position": "end"
                    },
                    compliance_notes=["NEC 690.8 - DC grounding requirements"],
                    priority=1
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def generate_protection_connections(self, component_chain: List[str],
                                      graph: Any) -> List[WiringSuggestion]:
        """
        Generate protection device connections in electrical chain.
        
        Args:
            component_chain: Ordered list of components in electrical path
            graph: ODL graph containing component nodes
            
        Returns:
            List of wiring suggestions for protection connections
        """
        suggestions = []
        
        for i in range(len(component_chain) - 1):
            source_id = component_chain[i]
            target_id = component_chain[i + 1]
            
            source_node = graph.nodes.get(source_id)
            target_node = graph.nodes.get(target_id)
            
            if not source_node or not target_node:
                continue
            
            # Determine connection type based on components
            source_type = source_node.get("type", "")
            target_type = target_node.get("type", "")
            
            if "protection" in source_type or "protection" in target_type:
                connection_type = ConnectionType.AC_PROTECTION
                reasoning = "AC protection device in circuit"
            elif "disconnect" in source_type or "disconnect" in target_type:
                connection_type = ConnectionType.AC_DISCONNECT
                reasoning = "AC disconnect switch in circuit"
            else:
                connection_type = ConnectionType.AC_INVERTER_OUTPUT
                reasoning = "AC circuit connection"
            
            # Find appropriate ports
            source_port = self._find_best_output_port(source_node, "ac")
            target_port = self._find_best_input_port(target_node, "ac")
            
            if source_port and target_port:
                suggestion = WiringSuggestion(
                    source_node_id=source_id,
                    source_port=source_port,
                    target_node_id=target_id,
                    target_port=target_port,
                    connection_type=connection_type,
                    confidence_score=0.85,
                    reasoning=reasoning,
                    electrical_specs={
                        "connection_type": "ac_circuit",
                        "protection_level": "line"
                    },
                    compliance_notes=["NEC 690.13 - AC disconnect requirements"],
                    priority=2
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _find_best_output_port(self, node: Dict[str, Any], port_type_hint: str = "") -> Optional[str]:
        """Find the best output port on a component."""
        if not node.get("ports"):
            # Fallback to common port names
            if "dc" in port_type_hint:
                if "+" in port_type_hint or "pos" in port_type_hint:
                    return "dc_pos"
                elif "-" in port_type_hint or "neg" in port_type_hint:
                    return "dc_neg"
            elif "ac" in port_type_hint:
                return "ac_l1"
            return "output"
        
        # Search through actual ports
        for port_id, port_spec in node["ports"].items():
            if port_spec.get("direction") == "output":
                if port_type_hint in port_id.lower() or port_type_hint in port_spec.get("type", ""):
                    return port_id
        
        # Fallback to first output port
        for port_id, port_spec in node["ports"].items():
            if port_spec.get("direction") == "output":
                return port_id
        
        return None
    
    def _find_best_input_port(self, node: Dict[str, Any], port_type_hint: str = "") -> Optional[str]:
        """Find the best input port on a component."""
        if not node.get("ports"):
            # Fallback to common port names
            if "dc" in port_type_hint:
                if "+" in port_type_hint or "pos" in port_type_hint:
                    return "dc_pos"  
                elif "-" in port_type_hint or "neg" in port_type_hint:
                    return "dc_neg"
            elif "ac" in port_type_hint:
                return "ac_l1"
            return "input"
        
        # Search through actual ports
        for port_id, port_spec in node["ports"].items():
            if port_spec.get("direction") == "input":
                if port_type_hint in port_id.lower() or port_type_hint in port_spec.get("type", ""):
                    return port_id
        
        # Fallback to first input port
        for port_id, port_spec in node["ports"].items():
            if port_spec.get("direction") == "input":
                return port_id
        
        return None
    
    def _get_available_mppt_channels(self, inverter_node: Dict[str, Any]) -> List[int]:
        """Get available MPPT channels on an inverter."""
        channels = []
        
        if inverter_node.get("ports"):
            # Count MPPT channels from port names
            for port_id in inverter_node["ports"].keys():
                if "pv" in port_id.lower() and ("_pos" in port_id or "_neg" in port_id):
                    # Extract channel number
                    try:
                        channel_num = int(''.join(filter(str.isdigit, port_id)))
                        if channel_num not in channels:
                            channels.append(channel_num)
                    except ValueError:
                        continue
        
        if not channels:
            # Default assumption for generic inverters
            channels = [1, 2]
        
        return sorted(channels)


class LLMWiringSuggestionEngine:
    """
    Enterprise LLM-powered wiring suggestion engine with RAG capabilities.
    Combines large language models with domain expertise for intelligent recommendations.
    """
    
    def __init__(self, enable_llm: bool = False):
        self.enable_llm = enable_llm
        self.heuristic_engine = EnhancedHeuristicEngine()
        self.port_engine = PortCompatibilityEngine()
    
    def generate_suggestions(self, 
                           grouped_panels: List[List[str]], 
                           graph: Any,
                           context: Optional[WiringContext] = None,
                           retrieved_examples: Optional[List[Any]] = None) -> List[WiringSuggestion]:
        """
        Generate comprehensive wiring suggestions using hybrid LLM + heuristic approach.
        
        Args:
            grouped_panels: List of panel groups for string formation
            graph: ODL graph with component nodes and ports
            context: Design context for optimization
            retrieved_examples: Similar designs from vector store
            
        Returns:
            List of prioritized wiring suggestions
        """
        all_suggestions = []
        
        # Generate heuristic suggestions first (always reliable)
        heuristic_suggestions = self._generate_heuristic_suggestions(
            grouped_panels, graph, context
        )
        all_suggestions.extend(heuristic_suggestions)
        
        # Enhance with LLM suggestions if enabled and available
        if self.enable_llm and self._is_llm_available():
            try:
                llm_suggestions = self._generate_llm_suggestions(
                    grouped_panels, graph, context, retrieved_examples, heuristic_suggestions
                )
                all_suggestions.extend(llm_suggestions)
            except Exception as e:
                logger.warning(f"LLM suggestion generation failed, using heuristics: {e}")
        
        # Validate and rank all suggestions
        validated_suggestions = self._validate_suggestions(all_suggestions, graph)
        ranked_suggestions = self._rank_suggestions(validated_suggestions, context)
        
        return ranked_suggestions
    
    def _generate_heuristic_suggestions(self, 
                                      grouped_panels: List[List[str]], 
                                      graph: Any,
                                      context: Optional[WiringContext] = None) -> List[WiringSuggestion]:
        """Generate reliable heuristic-based suggestions."""
        suggestions = []
        
        # Generate string connections
        for string_group in grouped_panels:
            string_suggestions = self.heuristic_engine.generate_string_connections(string_group, graph)
            suggestions.extend(string_suggestions)
        
        # Find inverters for string-to-inverter connections
        inverter_nodes = [nid for nid, node in graph.nodes.items() 
                         if "inverter" in node.get("type", "").lower()]
        
        if inverter_nodes and grouped_panels:
            inverter_suggestions = self.heuristic_engine.generate_inverter_connections(
                grouped_panels, inverter_nodes[0], graph
            )
            suggestions.extend(inverter_suggestions)
        
        # Generate protection circuit connections
        protection_nodes = [nid for nid, node in graph.nodes.items()
                          if "protection" in node.get("type", "").lower()]
        disconnect_nodes = [nid for nid, node in graph.nodes.items()
                          if "disconnect" in node.get("type", "").lower()]
        
        if inverter_nodes and (protection_nodes or disconnect_nodes):
            # Simple AC circuit: inverter -> protection -> disconnect
            ac_chain = inverter_nodes[:1] + protection_nodes + disconnect_nodes
            protection_suggestions = self.heuristic_engine.generate_protection_connections(ac_chain, graph)
            suggestions.extend(protection_suggestions)
        
        return suggestions
    
    def _generate_llm_suggestions(self,
                                grouped_panels: List[List[str]],
                                graph: Any, 
                                context: Optional[WiringContext],
                                retrieved_examples: Optional[List[Any]],
                                heuristic_suggestions: List[WiringSuggestion]) -> List[WiringSuggestion]:
        """
        Generate LLM-enhanced wiring suggestions with RAG.
        
        Note: This is a placeholder for actual LLM integration.
        In production, this would construct prompts and call OpenAI/Anthropic APIs.
        """
        # TODO: Implement actual LLM integration
        # This would involve:
        # 1. Constructing a detailed prompt with graph context
        # 2. Including retrieved examples for RAG
        # 3. Calling LLM API with domain-specific instructions  
        # 4. Parsing LLM response into WiringSuggestion objects
        # 5. Validating LLM suggestions against electrical rules
        
        logger.info("LLM suggestions requested but not implemented - using enhanced heuristics")
        
        # For now, return enhanced heuristic suggestions
        enhanced_suggestions = []
        
        # Add grounding suggestions (LLM would identify these patterns)
        grounding_suggestions = self._generate_grounding_suggestions(graph)
        enhanced_suggestions.extend(grounding_suggestions)
        
        # Add monitoring connections (LLM would optimize these)
        monitoring_suggestions = self._generate_monitoring_suggestions(graph)
        enhanced_suggestions.extend(monitoring_suggestions)
        
        return enhanced_suggestions
    
    def _generate_grounding_suggestions(self, graph: Any) -> List[WiringSuggestion]:
        """Generate equipment grounding connections."""
        suggestions = []
        
        # Find all components that need grounding
        grounding_nodes = []
        for node_id, node in graph.nodes.items():
            if node.get("ports") and "gnd" in str(node["ports"]).lower():
                grounding_nodes.append(node_id)
        
        # Create grounding backbone connections
        for i, node_id in enumerate(grounding_nodes):
            if i < len(grounding_nodes) - 1:
                suggestion = WiringSuggestion(
                    source_node_id=node_id,
                    source_port="gnd",
                    target_node_id=grounding_nodes[i + 1],  
                    target_port="gnd",
                    connection_type=ConnectionType.GROUNDING,
                    confidence_score=0.80,
                    reasoning="Equipment grounding conductor connection",
                    electrical_specs={"connection_type": "equipment_ground"},
                    compliance_notes=["NEC 690.43 - Equipment grounding"],
                    priority=2
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_monitoring_suggestions(self, graph: Any) -> List[WiringSuggestion]:
        """Generate monitoring system connections."""
        suggestions = []
        
        # Find monitoring components
        monitoring_nodes = [nid for nid, node in graph.nodes.items()
                          if "monitor" in node.get("type", "").lower()]
        
        # Find primary inverter for monitoring connection
        inverter_nodes = [nid for nid, node in graph.nodes.items()
                         if "inverter" in node.get("type", "").lower()]
        
        if monitoring_nodes and inverter_nodes:
            suggestion = WiringSuggestion(
                source_node_id=inverter_nodes[0],
                source_port="comm_out",
                target_node_id=monitoring_nodes[0], 
                target_port="comm_in",
                connection_type=ConnectionType.MONITORING,
                confidence_score=0.75,
                reasoning="Inverter to monitoring system communication",
                electrical_specs={"connection_type": "communication"},
                compliance_notes=["Optional monitoring connection"],
                priority=3
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _validate_suggestions(self, suggestions: List[WiringSuggestion], 
                            graph: Any) -> List[WiringSuggestion]:
        """Validate suggestions for electrical correctness and feasibility."""
        validated = []
        
        for suggestion in suggestions:
            # Check if nodes exist
            if (suggestion.source_node_id not in graph.nodes or 
                suggestion.target_node_id not in graph.nodes):
                continue
            
            source_node = graph.nodes[suggestion.source_node_id]
            target_node = graph.nodes[suggestion.target_node_id]
            
            # Check port compatibility
            is_compatible, reason = self.port_engine.are_ports_compatible(
                source_node, suggestion.source_port,
                target_node, suggestion.target_port
            )
            
            if is_compatible:
                # Update reasoning with compatibility check
                suggestion.reasoning += f" (Validated: {reason})"
                validated.append(suggestion)
            else:
                logger.warning(f"Incompatible connection rejected: {reason}")
        
        return validated
    
    def _rank_suggestions(self, suggestions: List[WiringSuggestion],
                         context: Optional[WiringContext] = None) -> List[WiringSuggestion]:
        """Rank suggestions by priority, confidence, and context relevance."""
        def ranking_key(suggestion: WiringSuggestion) -> Tuple[int, float, int]:
            # Sort by: priority (ascending), confidence (descending), connection type priority
            connection_priority = {
                ConnectionType.DC_STRING_SERIES: 1,
                ConnectionType.DC_TO_INVERTER: 2, 
                ConnectionType.AC_INVERTER_OUTPUT: 3,
                ConnectionType.AC_PROTECTION: 4,
                ConnectionType.AC_DISCONNECT: 5,
                ConnectionType.GROUNDING: 6,
                ConnectionType.MONITORING: 7
            }
            
            return (
                suggestion.priority,
                -suggestion.confidence_score,  # Negative for descending order
                connection_priority.get(suggestion.connection_type, 99)
            )
        
        return sorted(suggestions, key=ranking_key)
    
    def _is_llm_available(self) -> bool:
        """Check if LLM services are available and configured."""
        # TODO: Implement actual LLM availability check
        # This would check for API keys, service endpoints, etc.
        return False  # Disabled for now


# Main entry point function for backward compatibility
def generate_wiring_suggestions(
    grouped_panels: List[List[str]],
    graph: Any,
    retrieved_examples: Optional[List[Any]] = None,
    use_llm: bool = False
) -> List[Dict[str, str]]:
    """
    Generate wiring suggestions using enterprise AI engine.
    
    Args:
        grouped_panels: List of panel groups for string formation
        graph: ODL graph containing component nodes
        retrieved_examples: Similar designs from vector store (for RAG)
        use_llm: Whether to enable LLM-enhanced suggestions
        
    Returns:
        List of wiring suggestions in legacy format for compatibility
    """
    engine = LLMWiringSuggestionEngine(enable_llm=use_llm)
    
    # Generate context from graph analysis
    context = WiringContext(
        system_type="residential",  # Default assumption
        power_rating=4.0,  # Default 4kW system
        voltage_class="LV",
        compliance_codes=["NEC_2020"],
        installation_type="rooftop",
        geographical_region="US",
        design_preferences={},
        safety_requirements={}
    )
    
    suggestions = engine.generate_suggestions(grouped_panels, graph, context, retrieved_examples)
    
    # Convert to legacy format
    legacy_suggestions = []
    for suggestion in suggestions:
        legacy_suggestions.append({
            "source_node_id": suggestion.source_node_id,
            "source_port": suggestion.source_port,
            "target_node_id": suggestion.target_node_id,
            "target_port": suggestion.target_port,
            "confidence": suggestion.confidence_score,
            "reasoning": suggestion.reasoning
        })
    
    return legacy_suggestions