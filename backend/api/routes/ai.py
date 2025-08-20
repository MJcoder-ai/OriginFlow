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
