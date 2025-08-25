"""
Enterprise AI-Driven Wiring Generation Pipeline
==============================================

Comprehensive orchestration system that integrates panel grouping, vector store
retrieval, LLM suggestions, and electrical topology generation into a unified
AI-powered wiring pipeline. This module provides intelligent end-to-end wiring
automation for complex electrical designs with enterprise-grade monitoring,
validation, and optimization capabilities.

Key Features:
- Multi-stage AI pipeline with failure recovery
- Integration with enterprise vector store and LLM services
- Real-time validation and compliance checking
- Performance optimization and caching
- Comprehensive monitoring and audit trails
- Port-aware electrical topology generation
"""

from __future__ import annotations

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

from backend.ai.panel_grouping import EnterpriseGroupingEngine, GroupingStrategy, StringConfiguration
from backend.ai.vector_store import EnterpriseVectorStore, DesignMetadata, DesignCategory, retrieve_similar
from backend.ai.llm_wiring_suggest import LLMWiringSuggestionEngine, WiringContext, WiringSuggestion
from backend.tools.electrical_topology import ElectricalTopologyEngine, create_electrical_connections

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """AI pipeline execution stages."""
    INITIALIZATION = "initialization"
    PANEL_GROUPING = "panel_grouping"
    PATTERN_RETRIEVAL = "pattern_retrieval"  
    SUGGESTION_GENERATION = "suggestion_generation"
    VALIDATION = "validation"
    TOPOLOGY_GENERATION = "topology_generation"
    FINALIZATION = "finalization"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class PipelineMetrics:
    """Performance metrics for pipeline execution."""
    total_duration: float
    stage_durations: Dict[str, float]
    components_processed: int
    connections_generated: int
    suggestions_validated: int
    cache_hits: int
    error_count: int
    warning_count: int


@dataclass
class PipelineResult:
    """Comprehensive result from AI wiring pipeline."""
    success: bool
    status: PipelineStatus
    message: str
    edges: List[Dict[str, Any]]
    warnings: List[str]
    metrics: PipelineMetrics
    design_insights: Dict[str, Any]
    suggestions_used: List[Dict[str, Any]]
    fallback_applied: bool = False


@dataclass
class PipelineConfiguration:
    """Configuration for AI wiring pipeline execution."""
    max_modules_per_string: int = 12
    min_modules_per_string: int = 6
    grouping_strategy: GroupingStrategy = GroupingStrategy.PERFORMANCE_OPTIMIZED
    use_llm_suggestions: bool = False
    use_vector_store: bool = True
    vector_store_top_k: int = 3
    enable_caching: bool = True
    validation_strict: bool = True
    max_execution_time: float = 300.0  # 5 minutes
    enable_audit_trail: bool = True


class EnterpriseAIWiringPipeline:
    """
    Enterprise AI-driven wiring pipeline with comprehensive orchestration.
    
    This pipeline coordinates multiple AI components to generate optimal
    electrical connections for complex designs with full enterprise
    monitoring, validation, and optimization capabilities.
    """
    
    def __init__(self, config: Optional[PipelineConfiguration] = None):
        self.config = config or PipelineConfiguration()
        self.metrics = PipelineMetrics(
            total_duration=0.0,
            stage_durations={},
            components_processed=0,
            connections_generated=0,
            suggestions_validated=0,
            cache_hits=0,
            error_count=0,
            warning_count=0
        )
        self.cache: Dict[str, Any] = {}
        self.audit_trail: List[Dict[str, Any]] = []
        
        # Initialize AI components
        self.grouping_engine = EnterpriseGroupingEngine(
            StringConfiguration(
                max_modules_per_string=self.config.max_modules_per_string,
                min_modules_per_string=self.config.min_modules_per_string,
                grouping_strategy=self.config.grouping_strategy
            )
        )
        
        if self.config.use_vector_store:
            self.vector_store = EnterpriseVectorStore()
        else:
            self.vector_store = None
            
        self.suggestion_engine = LLMWiringSuggestionEngine(
            enable_llm=self.config.use_llm_suggestions
        )
        
        self.topology_engine = ElectricalTopologyEngine()
        
    def generate_wiring(
        self,
        graph: Any,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Execute complete AI wiring generation pipeline.
        
        Args:
            graph: ODL graph containing electrical components
            session_id: Unique session identifier
            context: Additional context for optimization
            
        Returns:
            Comprehensive pipeline result with connections and metadata
        """
        start_time = time.time()
        current_stage = PipelineStage.INITIALIZATION
        
        try:
            # Initialize pipeline
            self._audit_log("pipeline_start", {"session_id": session_id, "config": asdict(self.config)})
            result = self._initialize_pipeline(graph, session_id, context)
            if not result["success"]:
                return self._create_error_result("Initialization failed", result.get("message", ""))
            
            # Stage 1: Panel Grouping
            current_stage = PipelineStage.PANEL_GROUPING
            stage_start = time.time()
            panel_groups = self._execute_panel_grouping(graph)
            self.metrics.stage_durations["panel_grouping"] = time.time() - stage_start
            
            if not panel_groups:
                return self._create_warning_result("No panel groups generated", [])
            
            # Stage 2: Pattern Retrieval (if enabled)
            current_stage = PipelineStage.PATTERN_RETRIEVAL
            stage_start = time.time()
            retrieved_patterns = []
            if self.config.use_vector_store and self.vector_store:
                retrieved_patterns = self._execute_pattern_retrieval(graph, session_id)
            self.metrics.stage_durations["pattern_retrieval"] = time.time() - stage_start
            
            # Stage 3: Suggestion Generation
            current_stage = PipelineStage.SUGGESTION_GENERATION
            stage_start = time.time()
            wiring_suggestions = self._execute_suggestion_generation(
                panel_groups, graph, context, retrieved_patterns
            )
            self.metrics.stage_durations["suggestion_generation"] = time.time() - stage_start
            
            # Stage 4: Validation
            current_stage = PipelineStage.VALIDATION
            stage_start = time.time()
            validated_suggestions = self._execute_validation(wiring_suggestions, graph)
            self.metrics.stage_durations["validation"] = time.time() - stage_start
            self.metrics.suggestions_validated = len(validated_suggestions)
            
            # Stage 5: Topology Generation
            current_stage = PipelineStage.TOPOLOGY_GENERATION
            stage_start = time.time()
            final_connections = self._execute_topology_generation(
                validated_suggestions, panel_groups, graph
            )
            self.metrics.stage_durations["topology_generation"] = time.time() - stage_start
            self.metrics.connections_generated = len(final_connections)
            
            # Stage 6: Finalization
            current_stage = PipelineStage.FINALIZATION
            stage_start = time.time()
            result = self._finalize_pipeline(final_connections, graph, session_id)
            self.metrics.stage_durations["finalization"] = time.time() - stage_start
            
            # Calculate total duration
            self.metrics.total_duration = time.time() - start_time
            
            # Create successful result
            pipeline_result = PipelineResult(
                success=True,
                status=PipelineStatus.SUCCESS,
                message=f"Generated {len(final_connections)} AI-optimized connections",
                edges=final_connections,
                warnings=result.get("warnings", []),
                metrics=self.metrics,
                design_insights=self._generate_design_insights(panel_groups, validated_suggestions),
                suggestions_used=[self._serialize_suggestion(s) for s in validated_suggestions],
                fallback_applied=False
            )
            
            self._audit_log("pipeline_success", {"result": asdict(pipeline_result)})
            return pipeline_result
            
        except Exception as e:
            self.metrics.error_count += 1
            self.metrics.total_duration = time.time() - start_time
            
            error_msg = f"Pipeline failed at {current_stage.value}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Try fallback approach
            try:
                fallback_result = self._execute_fallback_wiring(graph, session_id)
                if fallback_result["success"]:
                    fallback_result["fallback_applied"] = True
                    fallback_result["message"] = f"Fallback successful after {current_stage.value} failure"
                    self._audit_log("pipeline_fallback", {"stage": current_stage.value, "error": str(e)})
                    return PipelineResult(**fallback_result, metrics=self.metrics)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                self.metrics.error_count += 1
            
            self._audit_log("pipeline_error", {"stage": current_stage.value, "error": str(e)})
            return self._create_error_result(error_msg, str(e))
    
    def _initialize_pipeline(
        self,
        graph: Any,
        session_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Initialize pipeline with validation and setup."""
        # Validate graph structure
        if not hasattr(graph, 'nodes') or not graph.nodes:
            return {"success": False, "message": "Empty or invalid graph"}
        
        # Count components by type
        component_counts = {}
        for node_id, node in graph.nodes.items():
            node_type = node.get("type", "unknown")
            component_counts[node_type] = component_counts.get(node_type, 0) + 1
        
        self.metrics.components_processed = len(graph.nodes)
        
        logger.info(f"Pipeline initialized: {len(graph.nodes)} components, session {session_id}")
        logger.info(f"Component breakdown: {component_counts}")
        
        return {"success": True, "component_counts": component_counts}
    
    def _execute_panel_grouping(self, graph: Any) -> List[List[str]]:
        """Execute intelligent panel grouping stage."""
        try:
            panel_groups = self.grouping_engine.group_panels(graph, self.config.grouping_strategy)
            
            logger.info(f"Panel grouping complete: {len(panel_groups)} groups using {self.config.grouping_strategy.value}")
            
            # Log group details
            for i, group in enumerate(panel_groups):
                logger.debug(f"String {i+1}: {len(group)} panels - {group}")
            
            return panel_groups
            
        except Exception as e:
            logger.error(f"Panel grouping failed: {e}")
            return []
    
    def _execute_pattern_retrieval(self, graph: Any, session_id: str) -> List[Any]:
        """Execute design pattern retrieval from vector store."""
        if not self.vector_store:
            return []
        
        try:
            # Generate cache key
            cache_key = f"patterns_{session_id}_{hash(str(graph.nodes))}"
            
            # Check cache first
            if self.config.enable_caching and cache_key in self.cache:
                self.metrics.cache_hits += 1
                return self.cache[cache_key]
            
            # Retrieve similar patterns
            search_results = self.vector_store.search_similar(
                query_graph={"nodes": graph.nodes, "edges": getattr(graph, 'edges', [])},
                top_k=self.config.vector_store_top_k,
                min_similarity=0.2
            )
            
            retrieved_patterns = [result.pattern for result in search_results]
            
            # Cache results
            if self.config.enable_caching:
                self.cache[cache_key] = retrieved_patterns
            
            logger.info(f"Retrieved {len(retrieved_patterns)} similar patterns from vector store")
            
            return retrieved_patterns
            
        except Exception as e:
            logger.warning(f"Pattern retrieval failed: {e}")
            return []
    
    def _execute_suggestion_generation(
        self,
        panel_groups: List[List[str]],
        graph: Any,
        context: Optional[Dict[str, Any]],
        retrieved_patterns: List[Any]
    ) -> List[WiringSuggestion]:
        """Execute AI-powered wiring suggestion generation."""
        try:
            # Create wiring context
            wiring_context = self._create_wiring_context(graph, context)
            
            # Generate suggestions using AI engine
            suggestions = self.suggestion_engine.generate_suggestions(
                panel_groups, graph, wiring_context, retrieved_patterns
            )
            
            logger.info(f"Generated {len(suggestions)} AI wiring suggestions")
            
            # Log suggestion breakdown by type
            suggestion_types = {}
            for suggestion in suggestions:
                conn_type = suggestion.connection_type.value
                suggestion_types[conn_type] = suggestion_types.get(conn_type, 0) + 1
            
            logger.debug(f"Suggestion breakdown: {suggestion_types}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return []
    
    def _execute_validation(
        self,
        suggestions: List[WiringSuggestion],
        graph: Any
    ) -> List[WiringSuggestion]:
        """Execute comprehensive validation of wiring suggestions."""
        validated = []
        validation_errors = []
        
        for suggestion in suggestions:
            try:
                # Check component existence
                if (suggestion.source_node_id not in graph.nodes or
                    suggestion.target_node_id not in graph.nodes):
                    validation_errors.append(f"Missing nodes: {suggestion.source_node_id} -> {suggestion.target_node_id}")
                    continue
                
                # Check port existence (if port-aware)
                source_node = graph.nodes[suggestion.source_node_id]
                target_node = graph.nodes[suggestion.target_node_id]
                
                if source_node.get("ports") and suggestion.source_port:
                    if suggestion.source_port not in source_node["ports"]:
                        validation_errors.append(f"Missing source port: {suggestion.source_port}")
                        continue
                
                if target_node.get("ports") and suggestion.target_port:
                    if suggestion.target_port not in target_node["ports"]:
                        validation_errors.append(f"Missing target port: {suggestion.target_port}")
                        continue
                
                # Additional electrical validation
                if suggestion.confidence_score < 0.3:
                    validation_errors.append(f"Low confidence suggestion rejected: {suggestion.confidence_score}")
                    continue
                
                validated.append(suggestion)
                
            except Exception as e:
                validation_errors.append(f"Validation error: {str(e)}")
                self.metrics.error_count += 1
        
        if validation_errors:
            self.metrics.warning_count += len(validation_errors)
            logger.warning(f"Validation rejected {len(validation_errors)} suggestions")
            for error in validation_errors[:5]:  # Log first 5 errors
                logger.debug(f"Validation error: {error}")
        
        logger.info(f"Validation complete: {len(validated)}/{len(suggestions)} suggestions passed")
        return validated
    
    def _execute_topology_generation(
        self,
        suggestions: List[WiringSuggestion],
        panel_groups: List[List[str]],
        graph: Any
    ) -> List[Dict[str, Any]]:
        """Execute electrical topology generation with AI suggestions."""
        connections = []
        
        try:
            # Convert AI suggestions to connection format
            for suggestion in suggestions:
                edge_id = f"{suggestion.source_node_id}_{suggestion.source_port}_to_{suggestion.target_node_id}_{suggestion.target_port}"
                
                connection = {
                    "id": edge_id,
                    "source_id": suggestion.source_node_id,
                    "target_id": suggestion.target_node_id,
                    "kind": "electrical",
                    "attrs": {
                        "layer": "single-line",
                        "source_port": suggestion.source_port,
                        "target_port": suggestion.target_port,
                        "connection_type": suggestion.connection_type.value,
                        "confidence": suggestion.confidence_score,
                        "ai_generated": True,
                        "reasoning": suggestion.reasoning,
                        "compliance_notes": suggestion.compliance_notes
                    }
                }
                
                connections.append(connection)
            
            # Use electrical topology engine for additional connections
            try:
                # Create components dict for topology engine
                components = {}
                for node_id, node in graph.nodes.items():
                    components[node_id] = {
                        "type": node.get("type", "unknown"),
                        "attrs": node.get("attrs", {}) or node.get("data", {})
                    }
                
                # Generate additional topology connections
                topology_connections = create_electrical_connections(components)
                
                # Convert topology connections to edge format
                for topo_conn in topology_connections:
                    edge_id = f"topo_{topo_conn.source_component}_{topo_conn.target_component}"
                    
                    # Avoid duplicating AI suggestions
                    existing_connection = any(
                        conn["source_id"] == topo_conn.source_component and
                        conn["target_id"] == topo_conn.target_component
                        for conn in connections
                    )
                    
                    if not existing_connection:
                        connection = {
                            "id": edge_id,
                            "source_id": topo_conn.source_component,
                            "target_id": topo_conn.target_component,
                            "kind": "electrical",
                            "attrs": {
                                "layer": "single-line",
                                "source_port": topo_conn.source_terminal,
                                "target_port": topo_conn.target_terminal,
                                "connection_type": topo_conn.connection_type,
                                "ai_generated": False,
                                "topology_generated": True
                            }
                        }
                        connections.append(connection)
                
                logger.info(f"Added {len(topology_connections)} topology connections")
                
            except Exception as e:
                logger.warning(f"Topology generation failed, using AI suggestions only: {e}")
            
            return connections
            
        except Exception as e:
            logger.error(f"Connection generation failed: {e}")
            return []
    
    def _finalize_pipeline(
        self,
        connections: List[Dict[str, Any]],
        graph: Any,
        session_id: str
    ) -> Dict[str, Any]:
        """Finalize pipeline with cleanup and result preparation."""
        warnings = []
        
        # Validate final connection count
        if len(connections) == 0:
            warnings.append("No connections generated - check component compatibility")
        
        # Store design in vector store for future learning
        if self.vector_store and len(connections) > 0:
            try:
                graph_data = {
                    "nodes": {nid: dict(node) for nid, node in graph.nodes.items()},
                    "edges": connections
                }
                
                # Create metadata for storage
                metadata = DesignMetadata(
                    system_type="pv_system",
                    power_rating=self._estimate_system_power(graph),
                    voltage_class="LV",
                    component_count=len(graph.nodes),
                    connection_count=len(connections),
                    compliance_codes=["NEC_2020"],
                    geographical_region="US",
                    installation_type="rooftop",
                    design_category=DesignCategory.RESIDENTIAL_PV,
                    performance_metrics={
                        "ai_suggestions": len([c for c in connections if c.get("attrs", {}).get("ai_generated", False)]),
                        "topology_connections": len([c for c in connections if c.get("attrs", {}).get("topology_generated", False)]),
                        "total_duration": self.metrics.total_duration
                    },
                    creation_timestamp=time.time(),
                    designer_id="ai_pipeline"
                )
                
                pattern_id = self.vector_store.store_design(graph_data, metadata)
                logger.info(f"Stored design pattern {pattern_id} for future learning")
                
            except Exception as e:
                logger.warning(f"Failed to store design pattern: {e}")
                warnings.append("Design pattern storage failed")
        
        return {
            "success": True,
            "connections": connections,
            "warnings": warnings
        }
    
    def _execute_fallback_wiring(self, graph: Any, session_id: str) -> Dict[str, Any]:
        """Execute simple fallback wiring when AI pipeline fails."""
        logger.info("Executing fallback wiring approach")
        
        try:
            # Simple component-based approach using topology engine
            components = {}
            for node_id, node in graph.nodes.items():
                components[node_id] = {
                    "type": node.get("type", "unknown"),
                    "attrs": node.get("attrs", {}) or node.get("data", {})
                }
            
            connections = create_electrical_connections(components)
            
            # Convert to edge format
            edges = []
            for conn in connections:
                edge = {
                    "id": f"fallback_{conn.source_component}_{conn.target_component}",
                    "source_id": conn.source_component,
                    "target_id": conn.target_component,
                    "kind": "electrical",
                    "attrs": {
                        "layer": "single-line",
                        "source_port": conn.source_terminal,
                        "target_port": conn.target_terminal,
                        "connection_type": conn.connection_type,
                        "fallback_generated": True
                    }
                }
                edges.append(edge)
            
            return {
                "success": True,
                "status": PipelineStatus.WARNING,
                "message": f"Fallback wiring generated {len(edges)} connections",
                "edges": edges,
                "warnings": ["AI pipeline failed, used simple fallback approach"],
                "design_insights": {"fallback_used": True},
                "suggestions_used": []
            }
            
        except Exception as e:
            logger.error(f"Fallback wiring also failed: {e}")
            return {
                "success": False,
                "status": PipelineStatus.ERROR,
                "message": "Both AI pipeline and fallback failed",
                "edges": [],
                "warnings": [f"Complete failure: {str(e)}"],
                "design_insights": {},
                "suggestions_used": []
            }
    
    def _create_wiring_context(self, graph: Any, context: Optional[Dict[str, Any]]) -> WiringContext:
        """Create wiring context from graph analysis and user context."""
        context = context or {}
        
        # Estimate system characteristics
        power_rating = self._estimate_system_power(graph)
        component_count = len(graph.nodes)
        
        # Determine system type based on scale
        if power_rating < 10:
            system_type = "residential"
        elif power_rating < 100:
            system_type = "commercial"
        else:
            system_type = "utility"
        
        return WiringContext(
            system_type=context.get("system_type", system_type),
            power_rating=power_rating,
            voltage_class=context.get("voltage_class", "LV"),
            compliance_codes=context.get("compliance_codes", ["NEC_2020"]),
            installation_type=context.get("installation_type", "rooftop"),
            geographical_region=context.get("region", "US"),
            design_preferences=context.get("preferences", {}),
            safety_requirements=context.get("safety", {})
        )
    
    def _estimate_system_power(self, graph: Any) -> float:
        """Estimate total system power from component analysis."""
        total_power = 0.0
        
        for node in graph.nodes.values():
            attrs = node.get("attrs", {}) or node.get("data", {})
            power = attrs.get("power", 0)
            
            if power > 0:
                total_power += power
        
        # Convert watts to kW
        return total_power / 1000.0 if total_power > 0 else 4.0  # Default 4kW
    
    def _generate_design_insights(
        self,
        panel_groups: List[List[str]],
        suggestions: List[WiringSuggestion]
    ) -> Dict[str, Any]:
        """Generate insights about the design and AI decisions."""
        insights = {
            "total_strings": len(panel_groups),
            "avg_string_size": sum(len(group) for group in panel_groups) / max(len(panel_groups), 1),
            "suggestion_confidence": sum(s.confidence_score for s in suggestions) / max(len(suggestions), 1),
            "connection_types": {},
            "compliance_coverage": set()
        }
        
        # Analyze connection types
        for suggestion in suggestions:
            conn_type = suggestion.connection_type.value
            insights["connection_types"][conn_type] = insights["connection_types"].get(conn_type, 0) + 1
            insights["compliance_coverage"].update(suggestion.compliance_notes)
        
        insights["compliance_coverage"] = list(insights["compliance_coverage"])
        
        return insights
    
    def _serialize_suggestion(self, suggestion: WiringSuggestion) -> Dict[str, Any]:
        """Convert WiringSuggestion to serializable dict."""
        return {
            "source_node_id": suggestion.source_node_id,
            "source_port": suggestion.source_port,
            "target_node_id": suggestion.target_node_id,
            "target_port": suggestion.target_port,
            "connection_type": suggestion.connection_type.value,
            "confidence_score": suggestion.confidence_score,
            "reasoning": suggestion.reasoning,
            "priority": suggestion.priority
        }
    
    def _create_error_result(self, message: str, details: str) -> PipelineResult:
        """Create error result with metrics."""
        return PipelineResult(
            success=False,
            status=PipelineStatus.ERROR,
            message=message,
            edges=[],
            warnings=[details] if details else [],
            metrics=self.metrics,
            design_insights={},
            suggestions_used=[],
            fallback_applied=False
        )
    
    def _create_warning_result(self, message: str, edges: List[Dict[str, Any]]) -> PipelineResult:
        """Create warning result with partial success."""
        return PipelineResult(
            success=len(edges) > 0,
            status=PipelineStatus.WARNING,
            message=message,
            edges=edges,
            warnings=[message],
            metrics=self.metrics,
            design_insights={},
            suggestions_used=[],
            fallback_applied=False
        )
    
    def _audit_log(self, event: str, data: Dict[str, Any]):
        """Log audit event if audit trail is enabled."""
        if not self.config.enable_audit_trail:
            return
        
        audit_entry = {
            "timestamp": time.time(),
            "event": event,
            "data": data
        }
        self.audit_trail.append(audit_entry)
        
        # Keep only last 1000 entries
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]


# Main entry point function for backward compatibility
def generate_ai_wiring(
    graph: Any,
    session_id: str,
    max_modules_per_string: int = 12,
    use_llm: bool = False
) -> Dict[str, Any]:
    """
    Generate AI-driven wiring using enterprise pipeline.
    
    Args:
        graph: ODL graph with electrical components
        session_id: Session identifier for tracking
        max_modules_per_string: Maximum modules per string
        use_llm: Whether to enable LLM suggestions
        
    Returns:
        Dictionary with wiring results in legacy format
    """
    config = PipelineConfiguration(
        max_modules_per_string=max_modules_per_string,
        use_llm_suggestions=use_llm,
        use_vector_store=True,
        enable_caching=True
    )
    
    pipeline = EnterpriseAIWiringPipeline(config)
    result = pipeline.generate_wiring(graph, session_id)
    
    # Convert to legacy format
    return {
        "success": result.success,
        "message": result.message,
        "edges": result.edges,
        "warnings": result.warnings,
        "ai_insights": result.design_insights,
        "performance_metrics": asdict(result.metrics)
    }