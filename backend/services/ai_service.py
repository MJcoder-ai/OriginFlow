# backend/services/ai_service.py
"""Orchestrator for AI agents and validation."""
from __future__ import annotations

from typing import List

from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from openai import OpenAIError

from backend.agents.router_agent import RouterAgent
from backend.utils.openai_helpers import map_openai_error
from backend.schemas.ai import AiAction, AiActionType, BomReportPayload, PositionPayload
from backend.schemas.component import ComponentCreate
from backend.schemas.link import LinkCreate

limiter = Limiter(key_func=get_remote_address)


class AiOrchestrator:
    """High-level orchestrator coordinating agent calls."""

    router_agent = RouterAgent()

    async def process(
        self,
        command: str,
        design_snapshot: dict | None = None,
        recent_actions: list[dict] | None = None,
    ) -> List[AiAction]:
        """Run the router agent and validate the returned actions.

        The optional ``design_snapshot`` and ``recent_actions`` arguments
        are forwarded to the :class:`LearningAgent` so retrieval-based
        confidence scoring can use richer context.
        """

        try:
            raw = await self.router_agent.handle(command, design_snapshot or {})
        except (OpenAIError, ValueError) as err:
            raise map_openai_error(err)
        validated: List[AiAction] = []
        # Default heuristic confidence mapping.  These values are used
        # when no historical data is available.  A learning model
        # implemented in ``backend/agents/learning_agent.py`` may override
        # these values based on past approvals.
        _CONFIDENCE_MAP = {
            AiActionType.validation: 1.0,
            AiActionType.report: 1.0,
            AiActionType.update_position: 0.7,
            AiActionType.add_component: 0.5,
            AiActionType.add_link: 0.5,
            AiActionType.suggest_link: 0.3,
            AiActionType.remove_component: 0.4,
            AiActionType.remove_link: 0.4,
        }
        for action in raw:
            try:
                obj = AiAction.model_validate(action)
            except Exception as exc:  # pragma: no cover - defensive
                raise HTTPException(422, f"Invalid action schema: {exc}") from exc
            # assign initial heuristic confidence score
            obj.confidence = _CONFIDENCE_MAP.get(obj.action, 0.5)

            if obj.action == AiActionType.add_component:
                ComponentCreate(**obj.payload)
            elif obj.action == AiActionType.add_link:
                LinkCreate(**obj.payload)
            elif obj.action == AiActionType.update_position:
                PositionPayload(**obj.payload)
            elif obj.action == AiActionType.report:
                BomReportPayload(**obj.payload)
            validated.append(obj)

        # Apply learning-based confidence adjustments.  If historical data
        # exists for any of the action types, this will override the
        # heuristic values set above.  Import here to avoid circular
        # dependencies during module load.
        try:
            from backend.agents.learning_agent import LearningAgent  # type: ignore
            learner = LearningAgent()
            await learner.assign_confidence(
                validated,
                design_snapshot or {},
                recent_actions or [],
            )
        except Exception:
            # If the learning agent fails (e.g. DB not initialised), fall
            # back to heuristic values without crashing.
            pass

        # Apply confidence-driven autonomy: automatically approve high-confidence actions
        # and mark them for auto-execution instead of requiring human approval.
        auto_approved_actions = []
        pending_actions = []
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Applying confidence-driven autonomy to {len(validated)} actions")
        
        for action in validated:
            # Set confidence threshold based on action type risk level
            confidence_threshold = self._get_confidence_threshold(action.action)
            action_type = action.action.value if hasattr(action.action, 'value') else str(action.action)
            
            logger.info(f"Action {action_type}: confidence={action.confidence}, threshold={confidence_threshold}")
            
            if action.confidence and action.confidence >= confidence_threshold:
                # High confidence: mark as auto-approved
                action.auto_approved = True
                auto_approved_actions.append(action)
                logger.info(f"AUTO-APPROVED: {action_type} (confidence {action.confidence} >= {confidence_threshold})")
            else:
                # Low confidence: requires human approval
                action.auto_approved = False
                pending_actions.append(action)
                logger.info(f"MANUAL APPROVAL: {action_type} (confidence {action.confidence} < {confidence_threshold})")
        
        logger.info(f"Result: {len(auto_approved_actions)} auto-approved, {len(pending_actions)} pending manual approval")
        
        # Return all actions, but mark which ones are auto-approved
        return validated

    def _get_confidence_threshold(self, action_type: AiActionType) -> float:
        """Get confidence threshold for auto-approval based on action type risk level.
        
        Higher risk actions require higher confidence for auto-approval.
        Conservative thresholds ensure safety while enabling autonomy for routine tasks.
        """
        # Conservative thresholds - require high confidence for auto-approval
        # Lowered thresholds to make learning more responsive for testing
        risk_thresholds = {
            AiActionType.validation: 0.6,        # Safe to auto-validate 
            AiActionType.report: 0.6,            # Safe to auto-generate reports
            AiActionType.update_position: 0.75,  # Layout changes need high confidence
            AiActionType.add_component: 0.8,     # Component addition needs high confidence
            AiActionType.add_link: 0.8,          # Connections need high confidence
            AiActionType.remove_component: 0.9,  # Deletion is high risk
            AiActionType.remove_link: 0.9,       # Deletion is high risk
        }
        return risk_thresholds.get(action_type, 0.95)  # Default to very conservative

    @classmethod
    def dep(cls) -> "AiOrchestrator":
        """Return orchestrator instance for FastAPI dependency injection."""

        return cls()
