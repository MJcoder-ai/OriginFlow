from __future__ import annotations

"""Feedback service for logging AI actions and user decisions.

This module defines :class:`FeedbackServiceV2` which persists feedback
records using a fresh database session for each call.  The service avoids
reusing request-scoped sessions which can be closed by the time the
logging coroutine executes, a situation that previously triggered
``500 Internal Server Error`` responses under rapid successive API
calls.
"""

from pydantic import BaseModel, Field

from backend.database.session import SessionMaker
from backend.models.ai_action_log import AiActionLog


class FeedbackPayloadV2(BaseModel):
    """Schema for feedback logging used by :func:`FeedbackServiceV2`.

    The fields mirror those accepted by the API endpoint but are kept
    minimal here so that the service remains decoupled from FastAPI
    route definitions.
    """

    session_id: str | None = Field(None, description="Session identifier")
    user_prompt: str = Field(..., description="The natural language command")
    proposed_action: dict = Field(..., description="The proposed AiAction")
    user_decision: str = Field(
        ...,
        description="approved, rejected or auto",
        pattern="^(approved|rejected|auto)$",
    )


class FeedbackServiceV2:
    """Persist AI action feedback to the database.

    A new ``AsyncSession`` is created for each call to :meth:`log_feedback`
    to ensure the session is valid, preventing race conditions where a
    reused session may have already been closed.
    """

    def __init__(self) -> None:
        # The service does not hold onto a session instance.  Doing so can
        # lead to race conditions if the session is closed elsewhere.
        pass

    async def log_feedback(self, payload: FeedbackPayloadV2) -> None:
        """Store the provided feedback payload.

        Parameters
        ----------
        payload:
            The feedback information captured from the client.
        """

        async with SessionMaker() as session:
            entry = AiActionLog(
                session_id=payload.session_id,
                prompt_text=payload.user_prompt,
                proposed_action=payload.proposed_action,
                user_decision=payload.user_decision,
            )
            session.add(entry)
            await session.commit()
