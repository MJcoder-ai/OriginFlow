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

    async def process(self, command: str) -> List[AiAction]:
        """Run the router agent and validate the returned actions."""

        try:
            raw = await self.router_agent.handle(command)
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
            await learner.assign_confidence(validated)
        except Exception:
            # If the learning agent fails (e.g. DB not initialised), fall
            # back to heuristic values without crashing.
            pass

        return validated

    @classmethod
    def dep(cls) -> "AiOrchestrator":
        """Return orchestrator instance for FastAPI dependency injection."""

        return cls()
