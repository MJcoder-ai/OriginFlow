"""Feedback logging endpoints.

This module exposes a simple API to record user feedback on AI actions.
It accepts a JSON payload describing the proposed action and whether the
user approved or rejected it.  Entries are stored in the
``ai_action_log`` table for downstream learning and audit purposes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.models.ai_action_log import AiActionLog

router = APIRouter()


class FeedbackPayload(BaseModel):
    session_id: str | None = Field(
        None, description="Session or project identifier for correlation"
    )
    prompt_text: str | None = Field(
        None, description="Original natural language command from the user"
    )
    proposed_action: dict = Field(
        ..., description="The AiAction payload that was proposed"
    )
    user_decision: str = Field(
        ...,
        description="User decision about the action",
        pattern="^(approved|rejected|auto)$",
    )


@router.post(
    "/ai/log-feedback",
    status_code=status.HTTP_200_OK,
    tags=["ai"],
)
async def log_ai_feedback(
    payload: FeedbackPayload, session: AsyncSession = Depends(get_session)
) -> None:
    """Record the user's decision on an AI-suggested action."""
    entry = AiActionLog(
        session_id=payload.session_id,
        prompt_text=payload.prompt_text,
        proposed_action=payload.proposed_action,
        user_decision=payload.user_decision,
    )
    session.add(entry)
    try:
        await session.commit()
    except Exception as exc:  # pragma: no cover
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log feedback: {exc}",
        )
    return {"status": "ok"}
