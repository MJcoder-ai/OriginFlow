# backend/api/routes/ai.py
"""AI command endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import AiOrchestrator
from backend.schemas.ai import AiAction

router = APIRouter()


@router.post("/ai/command", response_model=list[AiAction])
async def ai_command(command: str, orchestrator: AiOrchestrator = Depends(AiOrchestrator.dep)) -> list[AiAction]:
    """Process a natural-language command via the AI orchestrator."""

    return await orchestrator.process(command)
