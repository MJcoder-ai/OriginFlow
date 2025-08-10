# backend/api/routes/ai.py
"""AI command endpoint."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Body

from backend.api.deps import AiOrchestrator
from backend.schemas.ai import (
    AiAction,
    AiCommandRequest,
    PlanResponse,
)
from backend.services.ai_service import limiter

# Import the dedicated planner agent.  This agent generates high-level
# task sequences and quick actions based on natural language commands.
from backend.agents.planner_agent import PlannerAgent

router = APIRouter()


@router.post("/ai/command", response_model=list[AiAction])
@limiter.limit("30/minute")
async def ai_command(
    request: Request,
    req: Annotated[AiCommandRequest, Body(embed=False)],  # explicit body param
    orchestrator: AiOrchestrator = Depends(AiOrchestrator.dep),
) -> list[AiAction]:
    """Process a natural-language command via the AI orchestrator."""

    return await orchestrator.process(req.command)


# -----------------------------------------------------------------------------
# High-level planning endpoint
#
# The /ai/plan endpoint accepts the same natural language command as
# /ai/command but returns a coarse-grained sequence of tasks rather than low
# level actions.  These tasks outline the steps the orchestrator will take
# to fulfil the user's request.  The endpoint also returns a set of quick
# actions that the user might perform next.  This stub implementation
# produces a static plan for demonstration purposes; integration with a
# dedicated planning agent is required for full functionality.

@router.post("/ai/plan", response_model=PlanResponse)
@limiter.limit("30/minute")
async def ai_plan(
    request: Request,
    req: Annotated[AiCommandRequest, Body(embed=False)],
    orchestrator: AiOrchestrator = Depends(AiOrchestrator.dep),
) -> PlanResponse:
    """Generate a high-level plan for the provided command.

    This implementation delegates planning to the ``PlannerAgent``.  It
    constructs a planner bound to a default session identifier (``"global"``)
    because ``/ai/plan`` does not operate on a per-session graph.  The
    planner performs simple keyword analysis and returns an ordered list of
    tasks along with optional quick actions.  Future versions may
    incorporate project snapshots and design rules.
    """

    # Instantiate a planner for a default global session.  Since the
    # PlannerAgent uses the session ID only for context retrieval, we
    # supply a placeholder value when no explicit session is available.
    planner = PlannerAgent("global")
    tasks, actions = await planner.create_plan(req.command)
    return PlanResponse(tasks=tasks, quick_actions=actions if actions else None)
