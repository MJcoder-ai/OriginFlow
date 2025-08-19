from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.ai import AiAction, AnalyzeCommandRequest
from backend.services.analyze_service import AnalyzeOrchestrator
from backend.services.ai_service import limiter
from backend.services.agent_hydrator import AgentHydrator
from backend.api.deps import get_session, get_current_user
from backend.api.deps_tenant import seed_tenant_context

router = APIRouter()


@router.post("/ai/analyze-design", response_model=list[AiAction], dependencies=[Depends(seed_tenant_context)])
@limiter.limit("20/minute")
async def analyze_design(
    request: Request,
    req: dict = Body(..., embed=False),
    orchestrator: AnalyzeOrchestrator = Depends(AnalyzeOrchestrator.dep),
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> list[AiAction]:
    parsed = AnalyzeCommandRequest.model_validate(req)
    tenant_id = getattr(user, "tenant_id", None) or "default"
    if await AgentHydrator.should_hydrate(session, tenant_id):
        specs = await AgentHydrator.overlay_specs_for_tenant(session, tenant_id)
        with AgentHydrator.temporary_overlay(specs):
            return await orchestrator.process(parsed)
    return await orchestrator.process(parsed)
