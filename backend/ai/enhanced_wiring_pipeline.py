"""
Enhanced AI Wiring Pipeline with Enterprise Logging

This module integrates the proposed enterprise logging system with the existing
AI wiring pipeline to provide comprehensive audit trails, compliance reporting,
and real-time progress tracking.
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Tuple
from datetime import datetime

from backend.ai.panel_grouping import group_panels
from backend.ai.vector_store import retrieve_similar  
from backend.ai.llm_wiring_suggest import generate_wiring_suggestions
from backend.tools.enterprise_electrical_topology import create_electrical_connections
from backend.schemas.odl import ODLEdge, ODLGraph
from backend.schemas.pipeline import (
    PipelineLog,
    PipelineLogEntry, 
    PipelineStage,
    LogLevel,
    ComplianceIssue,
    ComplianceIssueType,
    PerformanceMetric
)


def generate_enhanced_ai_wiring(
    graph: Any,
    session_id: str,
    max_modules_per_string: int = 12,
    min_modules_per_string: int = 2,
    use_llm: bool = False
) -> Tuple[Dict[str, Any], PipelineLog]:
    """
    Enhanced AI wiring generation with comprehensive enterprise logging.
    
    This integrates the proposed pipeline logging system while maintaining
    compatibility with the existing formal ODL schema architecture.
    
    Args:
        graph: Current ODLGraph with nodes and edges
        session_id: Design session identifier
        max_modules_per_string: Maximum modules per string
        min_modules_per_string: Minimum modules per string (compliance)
        use_llm: Whether to use LLM for suggestions
        
    Returns:
        Tuple of (wiring results dict, comprehensive pipeline log)
    """
    # Initialize enterprise pipeline log
    pipeline_log = PipelineLog(
        session_id=session_id,
        configuration={
            "max_modules_per_string": max_modules_per_string,
            "min_modules_per_string": min_modules_per_string,
            "use_llm": use_llm,
            "compliance_checks_enabled": True,
            "enterprise_topology": True
        }
    )
    
    # Initialize results structure
    results: Dict[str, Any] = {
        "success": True,
        "message": "",
        "edges": [],
        "warnings": [],
    }
    
    try:
        # Stage 1: Initialization
        pipeline_log.add_entry(
            PipelineStage.INITIALIZATION,
            "Starting enhanced AI wiring pipeline",
            LogLevel.INFO
        )
        
        component_counts = {}
        if hasattr(graph, 'nodes'):
            for node_id, node in graph.nodes.items():
                node_type = getattr(node, 'type', 'unknown')
                component_counts[node_type] = component_counts.get(node_type, 0) + 1
        
        pipeline_log.add_entry(
            PipelineStage.COMPONENT_ANALYSIS,
            f"Analyzed {len(graph.nodes)} components: {component_counts}",
            LogLevel.INFO
        )
        
        # Stage 2: Enhanced Panel Grouping
        start_time = time.time()
        pipeline_log.add_entry(
            PipelineStage.PANEL_GROUPING,
            f"Starting panel grouping (max: {max_modules_per_string}, min: {min_modules_per_string})",
            LogLevel.INFO
        )
        
        panel_groups = group_panels(
            graph, 
            max_per_string=max_modules_per_string
        )
        
        grouping_duration = (time.time() - start_time) * 1000
        pipeline_log.add_entry(
            PipelineStage.PANEL_GROUPING,
            f"Formed {len(panel_groups)} panel groups",
            LogLevel.INFO,
            duration_ms=grouping_duration
        )
        
        if not panel_groups:
            pipeline_log.add_entry(
                PipelineStage.PANEL_GROUPING,
                "No panels found for grouping",
                LogLevel.ERROR
            )
            results["success"] = False
            results["message"] = "No panels found for wiring"
            pipeline_log.complete_execution()
            return results, pipeline_log
        
        # Compliance check: String sizing validation
        compliance_issues_found = []
        for group_idx, group in enumerate(panel_groups):
            if len(group) < min_modules_per_string:
                issue_msg = f"String {group_idx + 1} has only {len(group)} module(s) (minimum {min_modules_per_string} required)"
                
                pipeline_log.add_compliance_issue(
                    ComplianceIssueType.STRING_SIZING,
                    issue_msg,
                    severity=LogLevel.COMPLIANCE,
                    component_ids=group,
                    code_reference="NEC 690.7(A) - String sizing requirements",
                    remediation="Adjust panel grouping to meet minimum string size or update inverter specifications"
                )
                compliance_issues_found.append(issue_msg)
        
        # Stage 3: Pattern Retrieval
        start_time = time.time()
        pipeline_log.add_entry(
            PipelineStage.PATTERN_RETRIEVAL,
            "Retrieving similar design patterns",
            LogLevel.INFO
        )
        
        try:
            retrieved = retrieve_similar(graph, top_n=3)
            retrieved_graphs = [g for (g, _meta) in retrieved]
            
            retrieval_duration = (time.time() - start_time) * 1000
            pipeline_log.add_entry(
                PipelineStage.PATTERN_RETRIEVAL,
                f"Retrieved {len(retrieved_graphs)} similar designs",
                LogLevel.INFO,
                duration_ms=retrieval_duration
            )
        except Exception as e:
            pipeline_log.add_entry(
                PipelineStage.PATTERN_RETRIEVAL,
                f"Pattern retrieval failed: {str(e)}",
                LogLevel.WARNING
            )
            retrieved_graphs = []
        
        # Stage 4: AI Suggestion Generation
        start_time = time.time()
        pipeline_log.add_entry(
            PipelineStage.SUGGESTION_GENERATION,
            f"Generating wiring suggestions (LLM: {'enabled' if use_llm else 'disabled'})",
            LogLevel.INFO
        )
        
        suggestions = generate_wiring_suggestions(
            panel_groups, 
            graph, 
            retrieved_examples=retrieved_graphs,
            use_llm=use_llm
        )
        
        suggestion_duration = (time.time() - start_time) * 1000
        pipeline_log.add_entry(
            PipelineStage.SUGGESTION_GENERATION,
            f"Generated {len(suggestions)} wiring suggestions",
            LogLevel.INFO,
            duration_ms=suggestion_duration
        )
        
        # Stage 5: Enterprise Topology Generation
        start_time = time.time()
        pipeline_log.add_entry(
            PipelineStage.TOPOLOGY_GENERATION,
            "Creating electrical connections with enterprise validation",
            LogLevel.INFO
        )
        
        generated_edges = create_electrical_connections(
            suggestions, 
            graph,
            connection_type="electrical"
        )
        
        topology_duration = (time.time() - start_time) * 1000
        pipeline_log.add_entry(
            PipelineStage.TOPOLOGY_GENERATION,
            f"Created {len(generated_edges)} validated connections",
            LogLevel.INFO,
            duration_ms=topology_duration
        )
        
        # Stage 6: Enterprise Validation
        pipeline_log.add_entry(
            PipelineStage.ENTERPRISE_VALIDATION,
            "Running enterprise compliance validation",
            LogLevel.INFO
        )
        
        validation_warnings = []
        for edge in generated_edges:
            # Check for formal ODL schema compliance
            if not hasattr(edge, 'source_id') or not hasattr(edge, 'target_id'):
                validation_warnings.append(f"Edge {edge.id} missing formal schema attributes")
            
            # Check for compliance metadata
            if hasattr(edge, 'attrs') and edge.attrs.get('compliance_checked'):
                compliance_notes = edge.attrs.get('compliance_notes', [])
                if compliance_notes:
                    pipeline_log.add_entry(
                        PipelineStage.ENTERPRISE_VALIDATION,
                        f"Edge {edge.id}: {len(compliance_notes)} compliance notes",
                        LogLevel.DEBUG
                    )
        
        if validation_warnings:
            for warning in validation_warnings:
                pipeline_log.add_entry(
                    PipelineStage.ENTERPRISE_VALIDATION,
                    warning,
                    LogLevel.WARNING
                )
        
        # Stage 7: Finalization
        pipeline_log.add_entry(
            PipelineStage.FINALIZATION,
            "Finalizing AI wiring generation",
            LogLevel.INFO
        )
        
        # Convert ODLEdge instances to serializable format for results
        serialized_edges = []
        for edge in generated_edges:
            if hasattr(edge, 'model_dump'):
                serialized_edges.append(edge.model_dump())
            else:
                # Fallback for dict-based edges
                serialized_edges.append(edge)
        
        results["edges"] = serialized_edges
        results["message"] = f"Generated {len(generated_edges)} AI-optimized connections"
        
        # Add compliance warnings to results
        if compliance_issues_found:
            results["warnings"].extend(compliance_issues_found)
        
        # Complete pipeline execution
        pipeline_log.complete_execution()
        
        # Add final summary
        pipeline_log.add_entry(
            PipelineStage.FINALIZATION,
            f"Pipeline completed successfully: {len(generated_edges)} connections, {len(compliance_issues_found)} compliance issues",
            LogLevel.INFO
        )
        
        return results, pipeline_log
        
    except Exception as e:
        # Log critical error
        pipeline_log.add_entry(
            PipelineStage.FINALIZATION,
            f"Pipeline failed with error: {str(e)}",
            LogLevel.ERROR
        )
        
        results["success"] = False
        results["message"] = f"AI wiring pipeline failed: {str(e)}"
        results["warnings"].append(str(e))
        
        pipeline_log.complete_execution()
        return results, pipeline_log


def export_pipeline_log_for_frontend(pipeline_log: PipelineLog) -> Dict[str, Any]:
    """
    Export pipeline log in format optimized for frontend consumption.
    
    This creates the log format that the frontend AI Wiring Log tab can consume
    to display real-time progress and compliance information.
    
    Args:
        pipeline_log: Enterprise pipeline log instance
        
    Returns:
        Frontend-optimized log data structure
    """
    return {
        "pipeline_info": {
            "id": pipeline_log.pipeline_id,
            "session_id": pipeline_log.session_id,
            "started_at": pipeline_log.started_at.isoformat(),
            "completed_at": pipeline_log.completed_at.isoformat() if pipeline_log.completed_at else None,
            "status": pipeline_log.status,
            "duration_ms": pipeline_log.execution_summary.total_duration_ms if pipeline_log.execution_summary else None
        },
        "timeline": [
            {
                "timestamp": entry.timestamp.isoformat(),
                "stage": entry.stage.value,
                "level": entry.level.value,
                "message": entry.message,
                "duration_ms": entry.duration_ms,
                "components": entry.component_ids
            }
            for entry in pipeline_log.entries
        ],
        "compliance_issues": [
            {
                "type": issue.issue_type.value,
                "severity": issue.severity.value,
                "message": issue.message,
                "code_reference": issue.code_reference,
                "components_affected": issue.component_ids,
                "remediation": issue.remediation,
                "risk_level": issue.risk_level,
                "requires_approval": issue.affects_approval
            }
            for issue in pipeline_log.compliance_issues
        ],
        "summary": {
            "total_stages": len(set(entry.stage for entry in pipeline_log.entries)),
            "total_entries": len(pipeline_log.entries),
            "compliance_issues": len(pipeline_log.compliance_issues),
            "critical_issues": len(pipeline_log.get_critical_issues()),
            "warnings": len([e for e in pipeline_log.entries if e.level == LogLevel.WARNING]),
            "errors": len([e for e in pipeline_log.entries if e.level == LogLevel.ERROR])
        },
        "configuration": pipeline_log.configuration,
        "exportable": True  # Flag for frontend export functionality
    }