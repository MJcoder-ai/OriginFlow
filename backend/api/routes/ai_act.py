"""
AI Orchestrator routes.

POST /ai/act → run a high-level task against the ODL session using the
single orchestrator with typed tools and risk gating.
"""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.orchestrator.router import ActArgs
from backend.orchestrator.orchestrator import Orchestrator
from backend.tools.ai_wiring import generate_ai_wiring_legacy as generate_ai_wiring
from backend.ai.enhanced_wiring_pipeline import generate_enhanced_ai_wiring, export_pipeline_log_for_frontend
from backend.odl.store import ODLStore

router = APIRouter(prefix="/ai", tags=["AI"])


class ActRequest(BaseModel):
    session_id: str
    task: str
    request_id: str = Field(..., description="Idempotency scope for tool op_ids")
    args: ActArgs = Field(default_factory=ActArgs)


@router.post("/act")
async def act(req: ActRequest, db: AsyncSession = Depends(get_session)):
    orch = Orchestrator()
    env = await orch.run(
        db=db,
        session_id=req.session_id,
        task=req.task,
        request_id=req.request_id,
        args=req.args,
    )
    return env


class AIWiringRequest(BaseModel):
    """Request for AI-driven wiring generation."""
    session_id: str = Field(..., description="ODL session identifier")
    max_modules_per_string: int = Field(12, description="Maximum modules per string", ge=1, le=20)
    min_modules_per_string: int = Field(2, description="Minimum modules per string for compliance", ge=1)
    use_llm: bool = Field(False, description="Whether to use LLM for advanced suggestions")
    context: dict = Field(default_factory=dict, description="Additional wiring context")


class EnhancedAIWiringRequest(BaseModel):
    """Enhanced request for AI wiring with enterprise logging."""
    session_id: str = Field(..., description="ODL session identifier")
    max_modules_per_string: int = Field(12, description="Maximum modules per string", ge=1, le=20)
    min_modules_per_string: int = Field(2, description="Minimum modules per string", ge=1)
    use_llm: bool = Field(False, description="Enable LLM-powered suggestions")
    enable_logging: bool = Field(True, description="Enable enterprise pipeline logging")
    context: dict = Field(default_factory=dict, description="Additional context")


class AIWiringResponse(BaseModel):
    """Response from AI wiring generation."""
    success: bool
    message: str
    edges_added: int
    warnings: list[str]
    performance_metrics: dict
    session_version: int


class EnhancedAIWiringResponse(BaseModel):
    """Enhanced response with enterprise logging for AI wiring generation."""
    success: bool
    message: str
    edges_added: int
    warnings: list[str]
    performance_metrics: dict
    session_version: int
    # Enterprise logging data
    log: dict = Field(..., description="Comprehensive pipeline execution log")
    compliance_summary: dict = Field(..., description="Compliance validation summary")
    export_available: bool = Field(True, description="Whether log export is available")


@router.post("/wiring", response_model=AIWiringResponse)
async def generate_ai_wiring_endpoint(
    req: AIWiringRequest, 
    db: AsyncSession = Depends(get_session)
):
    """
    Generate intelligent wiring connections using AI analysis.
    
    This endpoint uses the enterprise AI wiring pipeline to:
    1. Group panels into optimal strings using advanced algorithms
    2. Retrieve similar historical designs from vector store
    3. Generate wiring suggestions via LLM or heuristics
    4. Create formal ODL edges with proper validation
    5. Apply changes with optimistic concurrency control
    """
    store = ODLStore(db)
    
    try:
        # Fetch current graph state
        graph = await store.get_graph(req.session_id)
        if not graph:
            return AIWiringResponse(
                success=False,
                message="Session not found",
                edges_added=0,
                warnings=[],
                performance_metrics={},
                session_version=0
            )
        
        # Store initial edge count for comparison
        initial_edge_count = len(graph.edges)
        
        # Call AI wiring pipeline with enterprise features
        result = generate_ai_wiring(
            graph=graph,
            session_id=req.session_id,
            max_modules_per_string=req.max_modules_per_string,
            use_llm=req.use_llm
        )
        
        if result["success"]:
            # Update graph version for optimistic concurrency
            graph.update_version()
            
            # Persist updated graph with new edges
            await store.put_graph(graph)
            
            return AIWiringResponse(
                success=True,
                message=result["message"],
                edges_added=len(graph.edges) - initial_edge_count,
                warnings=result.get("warnings", []),
                performance_metrics=result.get("performance_metrics", {}),
                session_version=graph.version
            )
        else:
            return AIWiringResponse(
                success=False,
                message=result["message"],
                edges_added=0,
                warnings=result.get("warnings", []),
                performance_metrics={},
                session_version=graph.version
            )
            
    except Exception as e:
        return AIWiringResponse(
            success=False,
            message=f"AI wiring generation failed: {str(e)}",
            edges_added=0,
            warnings=[f"Unexpected error: {str(e)}"],
            performance_metrics={},
            session_version=0
        )


@router.post("/wiring/enhanced", response_model=EnhancedAIWiringResponse)
async def generate_enhanced_ai_wiring_endpoint(
    req: EnhancedAIWiringRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Generate intelligent wiring with comprehensive enterprise logging and audit trails.
    
    This enhanced endpoint provides:
    1. Real-time pipeline logging with detailed stage tracking
    2. Comprehensive compliance validation and reporting
    3. Enterprise audit trail with exportable logs
    4. Advanced AI features with configurable parameters
    5. Frontend-optimized log format for the AI Wiring Log tab
    """
    store = ODLStore(db)
    
    try:
        # Fetch current graph state
        graph = await store.get_graph(req.session_id)
        if not graph:
            # Return minimal response for missing session
            return EnhancedAIWiringResponse(
                success=False,
                message="Session not found",
                edges_added=0,
                warnings=[],
                performance_metrics={},
                session_version=0,
                log={
                    "pipeline_info": {"status": "failed", "session_id": req.session_id},
                    "timeline": [],
                    "compliance_issues": [],
                    "summary": {"total_stages": 0, "total_entries": 0, "compliance_issues": 0}
                },
                compliance_summary={"total_issues": 0, "critical_issues": 0},
                export_available=False
            )
        
        # Store initial state for comparison
        initial_edge_count = len(graph.edges)
        
        # Call enhanced AI wiring pipeline with enterprise logging
        result, pipeline_log = generate_enhanced_ai_wiring(
            graph=graph,
            session_id=req.session_id,
            max_modules_per_string=req.max_modules_per_string,
            min_modules_per_string=req.min_modules_per_string,
            use_llm=req.use_llm
        )
        
        # Convert pipeline log to frontend format
        frontend_log = export_pipeline_log_for_frontend(pipeline_log)
        
        # Create compliance summary
        compliance_summary = {
            "total_issues": len(pipeline_log.compliance_issues),
            "critical_issues": len(pipeline_log.get_critical_issues()),
            "string_sizing_issues": len([
                issue for issue in pipeline_log.compliance_issues
                if issue.issue_type.value == "string_sizing"
            ]),
            "electrical_code_issues": len([
                issue for issue in pipeline_log.compliance_issues
                if issue.issue_type.value == "electrical_code"
            ]),
            "requires_approval": any(issue.affects_approval for issue in pipeline_log.compliance_issues)
        }
        
        if result["success"]:
            # Update graph with new edges
            new_edges = []
            for edge_data in result["edges"]:
                # Convert edge data back to ODLEdge if needed
                if isinstance(edge_data, dict):
                    from backend.schemas.odl import ODLEdge
                    edge = ODLEdge(**edge_data)
                    graph.edges.append(edge)
                    new_edges.append(edge)
            
            # Update graph version for optimistic concurrency
            graph.update_version()
            
            # Persist updated graph
            await store.put_graph(graph)
            
            return EnhancedAIWiringResponse(
                success=True,
                message=result["message"],
                edges_added=len(result["edges"]),
                warnings=result.get("warnings", []),
                performance_metrics={
                    "total_duration_ms": pipeline_log.execution_summary.total_duration_ms if pipeline_log.execution_summary else 0,
                    "stages_completed": len(set(entry.stage for entry in pipeline_log.entries)),
                    "compliance_checks": len(pipeline_log.compliance_issues)
                },
                session_version=graph.version,
                log=frontend_log,
                compliance_summary=compliance_summary,
                export_available=True
            )
        else:
            return EnhancedAIWiringResponse(
                success=False,
                message=result["message"],
                edges_added=0,
                warnings=result.get("warnings", []),
                performance_metrics={
                    "total_duration_ms": pipeline_log.execution_summary.total_duration_ms if pipeline_log.execution_summary else 0,
                    "stages_completed": len(set(entry.stage for entry in pipeline_log.entries)),
                    "error_count": len([e for e in pipeline_log.entries if e.level.value == "error"])
                },
                session_version=graph.version,
                log=frontend_log,
                compliance_summary=compliance_summary,
                export_available=True
            )
            
    except Exception as e:
        # Create minimal error log for exceptions
        error_log = {
            "pipeline_info": {
                "status": "failed",
                "session_id": req.session_id,
                "error": str(e)
            },
            "timeline": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "stage": "initialization",
                    "level": "error",
                    "message": f"Pipeline failed with exception: {str(e)}"
                }
            ],
            "compliance_issues": [],
            "summary": {"total_stages": 1, "total_entries": 1, "errors": 1}
        }
        
        return EnhancedAIWiringResponse(
            success=False,
            message=f"Enhanced AI wiring generation failed: {str(e)}",
            edges_added=0,
            warnings=[f"Unexpected error: {str(e)}"],
            performance_metrics={},
            session_version=0,
            log=error_log,
            compliance_summary={"total_issues": 0, "critical_issues": 0},
            export_available=False
        )
