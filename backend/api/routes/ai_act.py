"""
AI Orchestrator routes.

POST /ai/act → run a high-level task against the ODL session using the
single orchestrator with typed tools and risk gating.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.orchestrator.router import ActArgs
from backend.orchestrator.orchestrator import Orchestrator
from backend.tools.ai_wiring import generate_ai_wiring_legacy as generate_ai_wiring
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
    use_llm: bool = Field(False, description="Whether to use LLM for advanced suggestions")
    context: dict = Field(default_factory=dict, description="Additional wiring context")


class AIWiringResponse(BaseModel):
    """Response from AI wiring generation."""
    success: bool
    message: str
    edges_added: int
    warnings: list[str]
    performance_metrics: dict
    session_version: int


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
