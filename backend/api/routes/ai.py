# backend/api/routes/ai.py
"""AI command endpoint."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Body

from backend.api.deps import AiOrchestrator
from backend.schemas.ai import AiAction, AiCommandRequest
from backend.services.ai_service import limiter

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
