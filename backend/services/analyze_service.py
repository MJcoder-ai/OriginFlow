from __future__ import annotations
import os

from openai import OpenAIError

from backend.services.ai_service import AiOrchestrator
from backend.schemas.ai import AnalyzeCommandRequest, AiAction, AiActionType
from backend.schemas.component import ComponentCreate
from backend.schemas.link import LinkCreate
from backend.utils.openai_helpers import map_openai_error
from backend.utils.observability import trace_span, record_metric


class AnalyzeOrchestrator(AiOrchestrator):
    """Orchestrator aware of the design snapshot."""

    async def process(self, req: AnalyzeCommandRequest) -> list[AiAction]:
        prompt = self._serialize_snapshot(req)
        try:
            raw = await self.router_agent.handle(
                f"{prompt}\n\n{req.command}", req.snapshot.model_dump()
            )
        except (OpenAIError, ValueError) as err:  # pragma: no cover - network error
            raise map_openai_error(err)
        actions = self._validate_actions(raw)
        try:
            from backend.agents.learning_agent import LearningAgent  # type: ignore
            learner = LearningAgent()
            await learner.assign_confidence(
                actions,
                req.snapshot.model_dump(),
                [],
            )
        except Exception:
            pass
        
        # Apply risk- and confidence-driven autonomy (gated by env flag)
        import logging
        logger = logging.getLogger(__name__)
        AI_AUTO_APPROVE = os.getenv("AI_AUTO_APPROVE", "false").lower() == "true"
        if AI_AUTO_APPROVE:
            logger.info(f"Applying risk-based autonomy to {len(actions)} actions")
            # Import here to avoid circular dependencies at module load time
            from backend.policy.risk_policy import RiskPolicy  # type: ignore
            # Measure how long it takes to determine auto-approval
            with trace_span("analyze_service.auto_approval", action_count=len(actions)):
                for action in actions:
                    # Use the risk policy to determine auto-approval; since AnalyzeOrchestrator
                    # does not propagate agent names, we default to a synthetic "analyze_agent".
                    auto = RiskPolicy.is_auto_approved(
                        agent_name="analyze_agent",
                        action_type=action.action,
                        confidence=action.confidence,
                    )
                    action.auto_approved = bool(auto)
                    # Record a metric for each approval decision
                    record_metric(
                        "action.auto_approved.decision",
                        1 if auto else 0,
                        {"type": action.action.value, "confidence": action.confidence},
                    )
                    logger.info(
                        f"{'AUTO-APPROVED' if auto else 'MANUAL APPROVAL'}: "
                        f"{action.action} (confidence {action.confidence})"
                    )
        else:
            logger.info("Risk-based autonomy disabled; routing all actions to human review")
            for action in actions:
                action.auto_approved = False
        
        return actions

    @staticmethod
    def _serialize_snapshot(req: AnalyzeCommandRequest) -> str:
        comp_lines = "\n".join(
            f'- Component: "{c.name}" (ID: {c.id}, Type: {c.type})'
            for c in req.snapshot.components
        )
        link_lines = "\n".join(
            f'- Link: {link.source_id} -> {link.target_id}' for link in req.snapshot.links
        )
        return (
            "The current design consists of:\n"
            f"{comp_lines or ' - none'}\n\n"
            "Existing connections:\n"
            f"{link_lines or ' - none'}"
        )

    @classmethod
    def dep(cls) -> "AnalyzeOrchestrator":
        return cls()

    def _validate_actions(self, raw: list[dict]) -> list[AiAction]:
        validated: list[AiAction] = []
        
        # Default heuristic confidence mapping - same as AiOrchestrator
        _CONFIDENCE_MAP = {
            AiActionType.validation: 1.0,
            AiActionType.report: 1.0,
            AiActionType.update_position: 0.7,
            AiActionType.add_component: 0.5,
            AiActionType.add_link: 0.5,
            AiActionType.suggest_link: 0.3,
            AiActionType.remove_component: 0.4,
        }
        
        for action in raw:
            obj = AiAction.model_validate(action)
            # Assign initial heuristic confidence score
            obj.confidence = _CONFIDENCE_MAP.get(obj.action, 0.5)
            
            if obj.action == AiActionType.add_component:
                ComponentCreate(**obj.payload)
            elif obj.action in (AiActionType.add_link, AiActionType.suggest_link):
                LinkCreate(**obj.payload)
            validated.append(obj)
        return validated

    def _get_confidence_threshold(self, action_type: AiActionType) -> float:
        """Get confidence threshold for auto-approval based on action type risk level.
        
        Same thresholds as AiOrchestrator for consistency.
        """
        risk_thresholds = {
            AiActionType.validation: 0.6,
            AiActionType.report: 0.6,
            AiActionType.update_position: 0.75,
            AiActionType.add_component: 0.8,
            AiActionType.add_link: 0.8,
            AiActionType.remove_component: 0.9,
            AiActionType.remove_link: 0.9,
        }
        return risk_thresholds.get(action_type, 0.95)
