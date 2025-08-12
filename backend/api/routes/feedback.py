# backend/api/routes/feedback.py
"""Enhanced feedback API endpoints for learning agent integration."""
from __future__ import annotations

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.auth.dependencies import AuthenticatedUser, get_current_user
from backend.agents.learning_agent import LearningAgent
from backend.schemas.ai import AiAction

router = APIRouter(prefix="/feedback", tags=["feedback"])


class CardFeedbackRequest(BaseModel):
    """Request model for design card feedback."""
    cardId: str
    feedback: str  # 'accepted' | 'rejected'
    reason: Optional[str] = None
    agent: Optional[str] = None
    confidence: Optional[float] = None


class ActionFeedbackRequest(BaseModel):
    """Request model for AI action feedback."""
    action: Dict[str, Any]
    feedback: str  # 'accepted' | 'rejected' | 'modified'
    context: Optional[Dict[str, Any]] = None


class ConfidenceExplanationRequest(BaseModel):
    """Request model for confidence explanation."""
    action: Dict[str, Any]


@router.post("/card")
async def submit_card_feedback(
    request: CardFeedbackRequest,
    session: AsyncSession = Depends(get_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Submit feedback for a design card."""
    
    # Initialize learning agent
    learning_agent = LearningAgent()
    
    try:
        # Create an AiAction from the card data (simplified)
        action = AiAction(
            action="card_suggestion",
            payload={"cardId": request.cardId, "agent": request.agent},
            confidence=request.confidence or 0.5
        )
        
        # Process the feedback
        await learning_agent.process_user_feedback(
            action=action,
            feedback=request.feedback,
            context={
                "user_id": str(current_user.id),
                "card_id": request.cardId,
                "reason": request.reason,
                "agent": request.agent
            }
        )
        
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process feedback: {str(e)}")


@router.post("/action")
async def submit_action_feedback(
    request: ActionFeedbackRequest,
    session: AsyncSession = Depends(get_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Submit feedback for an AI action."""
    
    learning_agent = LearningAgent()
    
    try:
        # Convert dict to AiAction
        action = AiAction(**request.action)
        
        # Add user context
        context = request.context or {}
        context.update({
            "user_id": str(current_user.id),
            "session_id": context.get("session_id"),
            "original_prompt": context.get("original_prompt", "")
        })
        
        # Process the feedback
        await learning_agent.process_user_feedback(
            action=action,
            feedback=request.feedback,
            context=context
        )
        
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process feedback: {str(e)}")


@router.post("/confidence/explain")
async def explain_confidence(
    request: ConfidenceExplanationRequest,
    session: AsyncSession = Depends(get_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Get detailed explanation of confidence score calculation."""
    
    learning_agent = LearningAgent()
    
    try:
        # Convert dict to AiAction
        action = AiAction(**request.action)
        
        # Get confidence explanation
        explanation = await learning_agent.get_confidence_explanation(action)
        
        return explanation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get explanation: {str(e)}")


@router.get("/metrics")
async def get_learning_metrics(
    session: AsyncSession = Depends(get_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Get learning agent performance metrics."""
    
    learning_agent = LearningAgent()
    
    try:
        metrics = await learning_agent.get_learning_metrics()
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/thresholds/{action_type}")
async def update_auto_execution_threshold(
    action_type: str,
    new_threshold: float,
    session: AsyncSession = Depends(get_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Update auto-execution threshold for an action type."""
    
    # Only allow admin users to modify thresholds
    if not getattr(current_user, 'is_superuser', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    learning_agent = LearningAgent()
    
    try:
        await learning_agent.update_auto_execution_threshold(action_type, new_threshold)
        return {
            "status": "success", 
            "message": f"Updated threshold for {action_type} to {new_threshold}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update threshold: {str(e)}")


@router.get("/thresholds")
async def get_auto_execution_thresholds(
    session: AsyncSession = Depends(get_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Get current auto-execution thresholds."""
    
    learning_agent = LearningAgent()
    
    return {
        "thresholds": learning_agent.AUTO_EXECUTION_THRESHOLDS,
        "enabled": learning_agent.enable_auto_execution
    }