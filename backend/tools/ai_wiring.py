"""
Enterprise AI-driven wiring tool with formal ODL schema integration.

This tool provides intelligent wiring generation using advanced AI algorithms
while maintaining full compatibility with the platform's tool architecture.
Returns proper ODLPatch operations for orchestrator integration.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
import logging

from backend.schemas.odl import ODLNode, ODLEdge, ODLGraph
from backend.schemas.pipeline import PipelineLog
from backend.odl.schemas import ODLPatch, PatchOp
from backend.tools.schemas import AIWiringInput
from backend.ai.wiring_ai_pipeline import EnterpriseAIWiringPipeline, PipelineConfiguration
from backend.ai.panel_grouping import GroupingStrategy

logger = logging.getLogger(__name__)


def generate_ai_wiring(input_data: AIWiringInput) -> ODLPatch:
    """
    Generate intelligent wiring using AI analysis and return formal ODLPatch.
    
    This tool follows platform conventions:
    1. Takes typed AIWiringInput with formal validation
    2. Uses enterprise AI pipeline for wiring generation
    3. Returns ODLPatch with proper operation IDs for persistence
    4. Maintains optimistic concurrency and audit trails
    
    Args:
        input_data: Validated input with nodes and wiring parameters
        
    Returns:
        ODLPatch with add_edges operations for generated connections
    """
    logger.info(f"AI wiring generation for session {input_data.session_id}")
    
    try:
        # Create temporary ODLGraph for AI pipeline
        temp_graph = ODLGraph(
            session_id=input_data.session_id,
            version=1,  # Temporary version
            nodes={node.id: node for node in input_data.view_nodes},
            edges=[]
        )
        
        # Configure AI pipeline based on input parameters
        grouping_strategy_map = {
            "spatial_proximity": GroupingStrategy.SPATIAL_PROXIMITY,
            "electrical_optimal": GroupingStrategy.ELECTRICAL_OPTIMAL,
            "shading_aware": GroupingStrategy.SHADING_AWARE,
            "performance_optimized": GroupingStrategy.PERFORMANCE_OPTIMIZED,
        }
        
        config = PipelineConfiguration(
            max_modules_per_string=input_data.max_modules_per_string,
            use_llm_suggestions=input_data.use_llm,
            grouping_strategy=grouping_strategy_map.get(
                input_data.grouping_strategy, 
                GroupingStrategy.PERFORMANCE_OPTIMIZED
            ),
            enable_vector_retrieval=True,
            enable_topology_generation=True,
            enable_design_storage=True
        )
        
        # Initialize enterprise AI pipeline
        pipeline = EnterpriseAIWiringPipeline(config)
        
        # Generate wiring with full enterprise features
        result = pipeline.generate_wiring(temp_graph, input_data.session_id)
        
        if not result.success:
            logger.warning(f"AI wiring failed: {result.message}")
            return ODLPatch(
                ops=[],
                warnings=result.warnings,
                metadata={
                    "tool": "ai_wiring",
                    "success": False,
                    "message": result.message,
                    "metrics": result.metrics.__dict__
                }
            )
        
        # Convert ODLEdge instances to PatchOp operations
        patch_ops = []
        for i, edge in enumerate(result.edges):
            op_id = f"{input_data.request_id}_ai_wiring_{i}"
            
            # Create add_edges operation with formal schema
            patch_op = PatchOp(
                op_id=op_id,
                op_type="add_edges",
                data={"edges": [edge.model_dump()]}
            )
            patch_ops.append(patch_op)
        
        # Create comprehensive metadata for audit trail
        metadata = {
            "tool": "ai_wiring",
            "session_id": input_data.session_id,
            "success": True,
            "edges_generated": len(result.edges),
            "pipeline_status": result.status.value,
            "design_insights": result.design_insights,
            "performance_metrics": {
                "processing_time": result.metrics.total_duration,
                "components_processed": result.metrics.components_processed,
                "suggestions_generated": result.metrics.suggestions_generated,
                "topology_connections": result.metrics.topology_connections,
                "error_count": result.metrics.error_count
            },
            "ai_features_used": {
                "llm_suggestions": config.use_llm_suggestions,
                "vector_retrieval": config.enable_vector_retrieval,
                "topology_generation": config.enable_topology_generation,
                "grouping_strategy": input_data.grouping_strategy
            }
        }
        
        logger.info(f"AI wiring success: {len(result.edges)} edges generated")
        
        return ODLPatch(
            ops=patch_ops,
            warnings=result.warnings,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"AI wiring tool error: {e}", exc_info=True)
        
        return ODLPatch(
            ops=[],
            warnings=[f"AI wiring generation failed: {str(e)}"],
            metadata={
                "tool": "ai_wiring",
                "success": False,
                "error": str(e),
                "session_id": input_data.session_id
            }
        )


def validate_ai_wiring_input(nodes: List[ODLNode]) -> List[str]:
    """
    Validate input nodes for AI wiring generation.
    
    Args:
        nodes: List of component nodes to validate
        
    Returns:
        List of validation warnings/errors
    """
    warnings = []
    
    # Check for minimum viable components
    panel_count = len([n for n in nodes if 'panel' in n.type.lower()])
    inverter_count = len([n for n in nodes if 'inverter' in n.type.lower()])
    
    if panel_count < 2:
        warnings.append(f"Only {panel_count} panels found - need at least 2 for string formation")
    
    if inverter_count == 0:
        warnings.append("No inverters found - wiring may be incomplete")
    
    # Check for spatial coordinates
    panels_with_coords = len([
        n for n in nodes 
        if 'panel' in n.type.lower() and 
           n.data.get('x') is not None and n.data.get('y') is not None
    ])
    
    if panels_with_coords < panel_count:
        missing = panel_count - panels_with_coords
        warnings.append(f"{missing} panels missing spatial coordinates - may affect grouping quality")
    
    return warnings


# Convenience function for backward compatibility with existing pipeline
def generate_ai_wiring_legacy(
    graph: Any,
    session_id: str,
    max_modules_per_string: int = 12,
    use_llm: bool = False
) -> Dict[str, Any]:
    """
    Legacy wrapper for existing AI wiring pipeline calls.
    
    This maintains backward compatibility while encouraging migration
    to the formal tool architecture.
    """
    # Create formal input
    nodes = list(graph.nodes.values()) if hasattr(graph, 'nodes') else []
    
    input_data = AIWiringInput(
        session_id=session_id,
        request_id=f"legacy_{session_id}",
        view_nodes=nodes,
        max_modules_per_string=max_modules_per_string,
        use_llm=use_llm,
        simulate=False
    )
    
    # Generate using formal tool
    patch = generate_ai_wiring(input_data)
    
    # Convert back to legacy format
    edges = []
    for op in patch.ops:
        if op.op_type == "add_edges" and "edges" in op.data:
            edges.extend(op.data["edges"])
    
    return {
        "success": patch.metadata.get("success", False),
        "message": patch.metadata.get("message", "AI wiring completed"),
        "edges": edges,
        "warnings": patch.warnings,
        "performance_metrics": patch.metadata.get("performance_metrics", {}),
        "formal_schema": True
    }