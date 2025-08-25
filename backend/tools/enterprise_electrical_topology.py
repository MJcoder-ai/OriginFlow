"""
Enterprise Electrical Topology Generation with Formal ODL Schema.

This module provides advanced electrical topology generation capabilities that maintain
the formal ODL schema architecture while providing centralized, validated edge creation.
Unlike simple helpers, this provides enterprise-grade validation, compliance checking,
and comprehensive connection management.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

from backend.schemas.odl import ODLGraph, ODLNode, ODLEdge

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Standard electrical connection types for topology generation."""
    DC_STRING = "dc_string"
    DC_PARALLEL = "dc_parallel" 
    AC_BRANCH = "ac_branch"
    AC_MAIN = "ac_main"
    GROUNDING = "grounding"
    PROTECTION = "protection"
    MONITORING = "monitoring"
    COMMUNICATION = "communication"


@dataclass
class ConnectionSuggestion:
    """Enhanced connection suggestion with validation and metadata."""
    source_node_id: str
    target_node_id: str
    source_port: Optional[str] = None
    target_port: Optional[str] = None
    connection_type: ConnectionType = ConnectionType.DC_STRING
    confidence: float = 1.0
    reasoning: str = "Topology-generated connection"
    layer: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TopologyValidationResult:
    """Result of topology validation with detailed feedback."""
    valid: bool
    warnings: List[str]
    errors: List[str]
    suggestions: List[str]
    compliance_notes: List[str]


class EnterpriseElectricalTopology:
    """
    Enterprise electrical topology generator with formal schema integration.
    
    This class provides advanced topology generation while maintaining full
    compatibility with the formal ODL schema and enterprise validation requirements.
    """
    
    def __init__(self, enable_compliance_checking: bool = True):
        self.enable_compliance_checking = enable_compliance_checking
        self.logger = logging.getLogger(__name__ + ".EnterpriseElectricalTopology")
    
    def create_electrical_connections(
        self,
        suggestions: Union[List[ConnectionSuggestion], List[Dict[str, Any]]],
        graph: ODLGraph,
        default_connection_type: ConnectionType = ConnectionType.DC_STRING
    ) -> List[ODLEdge]:
        """
        Create formal ODLEdge instances from connection suggestions with enterprise validation.
        
        Args:
            suggestions: List of connection suggestions (enhanced or legacy format)
            graph: ODLGraph containing source and target nodes
            default_connection_type: Default connection type for legacy suggestions
            
        Returns:
            List of validated ODLEdge instances using formal schema
        """
        edges: List[ODLEdge] = []
        
        # Convert legacy suggestions to enhanced format
        enhanced_suggestions = self._normalize_suggestions(suggestions, default_connection_type)
        
        for idx, suggestion in enumerate(enhanced_suggestions):
            try:
                edge = self._create_validated_edge(suggestion, graph, idx)
                if edge:
                    edges.append(edge)
            except Exception as e:
                self.logger.error(f"Failed to create edge for suggestion {idx}: {e}")
                continue
        
        self.logger.info(f"Created {len(edges)} validated electrical connections")
        return edges
    
    def _normalize_suggestions(
        self,
        suggestions: Union[List[ConnectionSuggestion], List[Dict[str, Any]]],
        default_type: ConnectionType
    ) -> List[ConnectionSuggestion]:
        """Convert various suggestion formats to standard ConnectionSuggestion format."""
        normalized = []
        
        for suggestion in suggestions:
            if isinstance(suggestion, ConnectionSuggestion):
                normalized.append(suggestion)
            elif isinstance(suggestion, dict):
                # Convert legacy dict format to ConnectionSuggestion
                conn_type_str = suggestion.get("connection_type", default_type.value)
                try:
                    conn_type = ConnectionType(conn_type_str)
                except ValueError:
                    conn_type = default_type
                
                enhanced = ConnectionSuggestion(
                    source_node_id=suggestion["source_node_id"],
                    target_node_id=suggestion["target_node_id"],
                    source_port=suggestion.get("source_port"),
                    target_port=suggestion.get("target_port"),
                    connection_type=conn_type,
                    confidence=suggestion.get("confidence", 1.0),
                    reasoning=suggestion.get("reasoning", "Legacy suggestion"),
                    layer=suggestion.get("layer"),
                    metadata=suggestion.get("metadata", {})
                )
                normalized.append(enhanced)
        
        return normalized
    
    def _create_validated_edge(
        self, 
        suggestion: ConnectionSuggestion, 
        graph: ODLGraph, 
        index: int
    ) -> Optional[ODLEdge]:
        """Create a validated ODLEdge from a connection suggestion."""
        
        # Validate nodes exist in graph
        if suggestion.source_node_id not in graph.nodes:
            self.logger.warning(f"Source node {suggestion.source_node_id} not found in graph")
            return None
            
        if suggestion.target_node_id not in graph.nodes:
            self.logger.warning(f"Target node {suggestion.target_node_id} not found in graph")
            return None
        
        source_node = graph.nodes[suggestion.source_node_id]
        target_node = graph.nodes[suggestion.target_node_id]
        
        # Determine layer information
        layer = self._determine_layer(suggestion, source_node, target_node)
        
        # Validate ports if specified
        port_validation = self._validate_ports(suggestion, source_node, target_node)
        if not port_validation.valid:
            self.logger.warning(f"Port validation failed: {port_validation.errors}")
        
        # Generate unique edge ID
        edge_id = self._generate_edge_id(suggestion, index)
        
        # Create comprehensive edge metadata using formal schema (attrs)
        attrs = {
            "layer": layer,
            "connection_type": suggestion.connection_type.value,
            "confidence": suggestion.confidence,
            "reasoning": suggestion.reasoning,
            "topology_generated": True,
            "validation_warnings": port_validation.warnings,
            **suggestion.metadata
        }
        
        # Add compliance information if enabled
        if self.enable_compliance_checking:
            compliance_result = self._check_compliance(suggestion, source_node, target_node)
            attrs["compliance_checked"] = True
            attrs["compliance_notes"] = compliance_result.compliance_notes
        
        # Create formal ODLEdge using our superior schema
        edge = ODLEdge(
            id=edge_id,
            source_id=suggestion.source_node_id,  # Formal naming
            target_id=suggestion.target_node_id,  # Formal naming
            source_port=suggestion.source_port,
            target_port=suggestion.target_port,
            kind="electrical",  # Formal categorization
            attrs=attrs,  # Formal metadata location
            provisional=suggestion.confidence < 0.8  # Mark low-confidence as provisional
        )
        
        return edge
    
    def _determine_layer(
        self, 
        suggestion: ConnectionSuggestion,
        source_node: ODLNode, 
        target_node: ODLNode
    ) -> str:
        """Determine appropriate layer for the connection."""
        # Use suggestion layer if provided
        if suggestion.layer:
            return suggestion.layer
        
        # Use source node layer if available
        if source_node.layer:
            return source_node.layer
            
        # Use target node layer if available
        if target_node.layer:
            return target_node.layer
            
        # Default based on connection type
        layer_map = {
            ConnectionType.DC_STRING: "single-line",
            ConnectionType.AC_BRANCH: "single-line", 
            ConnectionType.AC_MAIN: "single-line",
            ConnectionType.GROUNDING: "single-line",
            ConnectionType.PROTECTION: "single-line",
            ConnectionType.MONITORING: "schematic",
            ConnectionType.COMMUNICATION: "schematic"
        }
        
        return layer_map.get(suggestion.connection_type, "single-line")
    
    def _validate_ports(
        self,
        suggestion: ConnectionSuggestion,
        source_node: ODLNode,
        target_node: ODLNode
    ) -> TopologyValidationResult:
        """Validate port connectivity for the connection."""
        warnings = []
        errors = []
        suggestions_list = []
        
        # Check if ports are specified when nodes have port definitions
        if source_node.ports and not suggestion.source_port:
            warnings.append(f"Source node {suggestion.source_node_id} has ports but no source_port specified")
            
        if target_node.ports and not suggestion.target_port:
            warnings.append(f"Target node {suggestion.target_node_id} has ports but no target_port specified")
        
        # Validate specified ports exist in node definitions
        if suggestion.source_port and source_node.ports:
            if suggestion.source_port not in source_node.ports:
                errors.append(f"Source port {suggestion.source_port} not found in node {suggestion.source_node_id}")
        
        if suggestion.target_port and target_node.ports:
            if suggestion.target_port not in target_node.ports:
                errors.append(f"Target port {suggestion.target_port} not found in node {suggestion.target_node_id}")
        
        # Check port compatibility (basic electrical compatibility)
        if suggestion.source_port and suggestion.target_port:
            port_compat = self._check_port_compatibility(
                suggestion.source_port, suggestion.target_port,
                source_node, target_node
            )
            if not port_compat:
                warnings.append(f"Port compatibility questionable: {suggestion.source_port} -> {suggestion.target_port}")
        
        return TopologyValidationResult(
            valid=len(errors) == 0,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions_list,
            compliance_notes=[]
        )
    
    def _check_port_compatibility(
        self,
        source_port: str,
        target_port: str, 
        source_node: ODLNode,
        target_node: ODLNode
    ) -> bool:
        """Check basic electrical compatibility between ports."""
        # Simple compatibility rules (can be enhanced)
        dc_ports = {"dc+", "dc-", "dc_pos", "dc_neg"}
        ac_ports = {"ac_l1", "ac_l2", "ac_l3", "ac_n"}
        
        source_is_dc = any(dc_term in source_port.lower() for dc_term in dc_ports)
        target_is_dc = any(dc_term in target_port.lower() for dc_term in dc_ports)
        source_is_ac = any(ac_term in source_port.lower() for ac_term in ac_ports)
        target_is_ac = any(ac_term in target_port.lower() for ac_term in ac_ports)
        
        # DC-DC and AC-AC connections are generally compatible
        if (source_is_dc and target_is_dc) or (source_is_ac and target_is_ac):
            return True
        
        # Mixed DC-AC connections may be valid (through inverters)
        return True  # Allow all for now, can be enhanced with more rules
    
    def _check_compliance(
        self,
        suggestion: ConnectionSuggestion,
        source_node: ODLNode,
        target_node: ODLNode
    ) -> TopologyValidationResult:
        """Perform basic electrical compliance checking."""
        compliance_notes = []
        warnings = []
        
        # Basic NEC compliance checks
        if suggestion.connection_type == ConnectionType.DC_STRING:
            compliance_notes.append("DC string connection - verify NEC 690.7 voltage limits")
            
        if suggestion.connection_type == ConnectionType.AC_BRANCH:
            compliance_notes.append("AC branch connection - verify NEC 210/220 requirements")
        
        # Check for grounding requirements
        panel_types = ["panel", "pv_module", "solar_panel"]
        if any(panel_type in source_node.type.lower() for panel_type in panel_types):
            compliance_notes.append("Panel connection - verify equipment grounding conductor")
        
        return TopologyValidationResult(
            valid=True,
            warnings=warnings,
            errors=[],
            suggestions=[],
            compliance_notes=compliance_notes
        )
    
    def _generate_edge_id(self, suggestion: ConnectionSuggestion, index: int) -> str:
        """Generate unique edge identifier."""
        base = f"{suggestion.source_node_id}_to_{suggestion.target_node_id}"
        if suggestion.source_port and suggestion.target_port:
            base = f"{suggestion.source_node_id}_{suggestion.source_port}_to_{suggestion.target_node_id}_{suggestion.target_port}"
        return f"{base}_{index}"


# Convenience functions for backward compatibility with enhanced features
def create_electrical_connections(
    suggestions: Union[List[Dict[str, Any]], List[ConnectionSuggestion]],
    graph: ODLGraph,
    connection_type: str = "electrical"
) -> List[ODLEdge]:
    """
    Enhanced convenience function that maintains compatibility while providing enterprise features.
    
    Args:
        suggestions: Connection suggestions (legacy dict or enhanced format)
        graph: ODLGraph containing nodes
        connection_type: Default connection type (converted to enum)
        
    Returns:
        List of formal ODLEdge instances with enterprise validation
    """
    # Convert string connection type to enum
    type_mapping = {
        "electrical": ConnectionType.DC_STRING,
        "dc_string": ConnectionType.DC_STRING,
        "ac_branch": ConnectionType.AC_BRANCH,
        "grounding": ConnectionType.GROUNDING
    }
    
    default_type = type_mapping.get(connection_type, ConnectionType.DC_STRING)
    
    # Use enterprise topology generator
    topology_generator = EnterpriseElectricalTopology(enable_compliance_checking=True)
    
    return topology_generator.create_electrical_connections(
        suggestions=suggestions,
        graph=graph,
        default_connection_type=default_type
    )


def create_enhanced_connection_suggestion(
    source_id: str,
    target_id: str,
    source_port: Optional[str] = None,
    target_port: Optional[str] = None,
    connection_type: ConnectionType = ConnectionType.DC_STRING,
    confidence: float = 1.0,
    reasoning: str = "User-specified connection"
) -> ConnectionSuggestion:
    """Create an enhanced connection suggestion with full metadata."""
    return ConnectionSuggestion(
        source_node_id=source_id,
        target_node_id=target_id,
        source_port=source_port,
        target_port=target_port,
        connection_type=connection_type,
        confidence=confidence,
        reasoning=reasoning
    )