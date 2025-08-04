"""Feedback API v2 with enriched schema and vector upserts.

This module defines a versioned endpoint for recording user feedback on
AI actions with additional metadata.  It enriches the feedback
payload with anonymized prompts, contexts and session history,
embeds the resulting document and stores the vector in a vector
database.  The raw feedback is still stored in ``ai_action_log`` for
backwards compatibility.
"""
from __future__ import annotations

import base64
import os

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session, get_anonymizer, get_embedder
from backend.models.ai_action_log import AiActionLog
from backend.models.ai_action_vector import AiActionVector
from backend.services.anonymizer_service import AnonymizerService
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import VectorStore, get_vector_store
from backend.services import encryptor

router = APIRouter()


class FeedbackPayloadV2(BaseModel):
    session_id: str | None = Field(None, description="Session or project identifier")
    user_prompt: str = Field(..., description="The natural language command from the user")
    proposed_action: dict = Field(..., description="The proposed AiAction payload")
    user_decision: str = Field(..., description="approved, rejected or auto", pattern="^(approved|rejected|auto)$")
    component_type: str | None = Field(None, description="Type of component being added (if any)")
    design_context: dict | None = Field(None, description="Current design context as a JSON object")
    session_history: dict | None = Field(None, description="Recent actions and context history")
    confidence_shown: float | None = Field(None, description="Confidence displayed to the user")
    confirmed_by: str | None = Field(None, description="human or auto confirmation")


@router.post(
    "/ai/log-feedback-v2",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["ai"],
)
async def log_feedback_v2(
    payload: FeedbackPayloadV2,
    session: AsyncSession = Depends(get_session),
    anonymizer: AnonymizerService = Depends(get_anonymizer),
    embedder: EmbeddingService = Depends(get_embedder),
    store: VectorStore = Depends(get_vector_store),
) -> Response:
    """Record enriched user feedback and upsert a vector.

    This endpoint stores the raw log in ``ai_action_log`` and writes an
    anonymized, embedded record to the ``ai_action_vectors`` table and
    the vector store.  Any errors are rolled back and result in a
    500 response.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Starting log_feedback_v2 with payload: {payload.user_prompt[:50]}...")
    
    try:
        # Store the entire proposed action without coercing component IDs.
        # Some clients generate temporary string identifiers (e.g. "component_123"),
        # so casting them to integers would raise errors.  Persist the raw payload
        # and defer any interpretation to downstream consumers.
        logger.info("Creating AiActionLog entry...")
        entry = AiActionLog(
            session_id=payload.session_id,
            prompt_text=payload.user_prompt,
            proposed_action=payload.proposed_action,
            user_decision=payload.user_decision,
        )
        session.add(entry)
        
        logger.info("Anonymizing prompts and context...")
        anonymized_prompt = anonymizer.anonymize(payload.user_prompt or "")
        anonymized_ctx = anonymizer.anonymize_context(payload.design_context)
        
        logger.info("Creating embedding...")
        embedding = await embedder.embed_log(payload, anonymized_prompt, anonymized_ctx)
        
        logger.info("Processing encryption...")
        key = os.getenv("EMBEDDING_ENCRYPTION_KEY")
        embedding_db = embedding
        if key:
            try:
                encrypted = encryptor.encrypt_vector(embedding, key.encode())
                embedding_db = base64.b64encode(encrypted).decode("utf-8")
            except Exception as enc_exc:
                # fall back to plain embedding if encryption fails
                logger.warning(f"Encryption failed, using plain embedding: {enc_exc}")
                embedding_db = embedding
        
        logger.info("Creating AiActionVector entry...")
        vec_entry = AiActionVector(
            action_type=payload.proposed_action.get("action"),
            component_type=payload.component_type,
            user_prompt=payload.user_prompt,
            anonymized_prompt=anonymized_prompt,
            design_context=payload.design_context,
            anonymized_context=anonymized_ctx,
            session_history=payload.session_history,
            approval=payload.user_decision in ("approved", "auto"),
            confidence_shown=payload.confidence_shown,
            confirmed_by=payload.confirmed_by or "human",
            embedding=embedding_db,
            meta={"version": 1},
        )
        session.add(vec_entry)
        
        logger.info("Committing to database...")
        try:
            await session.commit()
            logger.info("Database commit successful")
        except Exception as exc:
            logger.error(f"Database commit failed: {exc}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to log feedback: {exc}",
            )
        
        # Try to upsert to vector store, but don't fail the entire request if this fails
        logger.info("Upserting to vector store...")
        try:
            await store.upsert(str(vec_entry.id), embedding, {
                "action_type": payload.proposed_action.get("action"),
                "component_type": payload.component_type,
                "approval": payload.user_decision in ("approved", "auto"),
                "user_prompt": payload.user_prompt,
                "design_context": payload.design_context,
            })
            logger.info("Vector store upsert successful")
        except Exception as exc:
            # Log the error but don't fail the request since the database operation succeeded
            logger.warning(f"Failed to upsert to vector store: {exc}")
        
        logger.info("log_feedback_v2 completed successfully")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except Exception as exc:
        logger.error(f"Unexpected error in log_feedback_v2: {exc}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        )
