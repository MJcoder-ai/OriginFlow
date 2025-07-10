from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Body

from backend.schemas.ai import AiAction, AnalyzeCommandRequest
from backend.services.analyze_service import AnalyzeOrchestrator
from backend.services.ai_service import limiter

router = APIRouter()


@router.post("/ai/analyze-design", response_model=list[AiAction])
@limiter.limit("20/minute")
async def analyze_design(
    request: Request,
    req: dict = Body(..., embed=False),
    orchestrator: AnalyzeOrchestrator = Depends(AnalyzeOrchestrator.dep),
) -> list[AiAction]:
    parsed = AnalyzeCommandRequest.model_validate(req)
    return await orchestrator.process(parsed)
