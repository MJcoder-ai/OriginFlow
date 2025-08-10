# backend/services/ai_service.py
"""Orchestrator for AI agents and validation."""
from __future__ import annotations

from typing import List
import uuid
import inspect

from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from openai import OpenAIError

from backend.agents.router_agent import RouterAgent
from backend.agents.registry import get_spec
from backend.utils.openai_helpers import map_openai_error
from backend.schemas.ai import AiAction, AiActionType, BomReportPayload, PositionPayload
from backend.schemas.component import ComponentCreate
from backend.schemas.link import LinkCreate
from backend.schemas.design_context import RequestContext, DesignSnapshot
from backend.policy.capabilities import ACTION_REQUIRED_SCOPES
from backend.services.ai_clients import get_openai_client
from backend.utils.logging import get_logger

limiter = Limiter(key_func=get_remote_address)


logger = get_logger(__name__)


def _check_capabilities(agent_name: str, action: AiAction) -> None:
    spec = get_spec(agent_name)
    required = ACTION_REQUIRED_SCOPES.get(action.action, [])
    missing = [s for s in required if s not in spec.capabilities]
    if missing:
        raise PermissionError(
            f"Agent '{agent_name}' lacks capability for {action.action}: missing {missing}"
        )


class AiOrchestrator:
    """High-level orchestrator coordinating agent calls."""

    router_agent = RouterAgent(get_openai_client())

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

        ctx = RequestContext(
            trace_id=str(uuid.uuid4()),
            snapshot=DesignSnapshot(**design_snapshot) if design_snapshot else None,
        )
        logger.info(
            "ai.process_command.start", trace_id=ctx.trace_id, agent_router="RouterAgent"
        )
        handle_params = inspect.signature(self.router_agent.handle).parameters
        kwargs: dict = {}
        if "snapshot" in handle_params:
            kwargs["snapshot"] = ctx.snapshot
        if "trace_id" in handle_params:
            kwargs["trace_id"] = ctx.trace_id
        try:
            raw = await self.router_agent.handle(command, **kwargs)
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
            agent_name = action.pop("agent_name", "unknown")
            try:
                obj = AiAction.model_validate(action)
            except Exception as exc:  # pragma: no cover - defensive
                raise HTTPException(422, f"Invalid action schema: {exc}") from exc
            _check_capabilities(agent_name, obj)
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

        # In the plan–act model all actions are auto-approved.  Set the flag
        # uniformly and emit tracing events (best effort) before returning.
        for action in validated:
            action.auto_approved = True
        auto_count = len(validated)

        try:  # Emit trace events; ignore any errors
            from backend.services.tracing import emit_event  # type: ignore
            from backend.database.session import SessionMaker  # type: ignore
            prev_sha = None
            async with SessionMaker() as trace_sess:  # type: ignore
                await emit_event(
                    trace_sess,
                    ctx.trace_id,
                    actor="RouterAgent",
                    event_type="router_result",
                    payload={"raw_actions": raw},
                    prev_sha=prev_sha,
                )
                for act in validated:
                    ev = await emit_event(
                        trace_sess,
                        ctx.trace_id,
                        actor=str(act.action.value),
                        event_type="ai_action",
                        payload={
                            "action": act.action.value,
                            "payload": act.payload,
                            "confidence": act.confidence,
                            "auto_approved": True,
                        },
                        prev_sha=prev_sha,
                    )
                    prev_sha = ev.sha256
        except Exception:
            pass

        # Best-effort memory logging; tags record number of auto-approved actions
        try:
            from backend.models.memory import Memory  # type: ignore
            from backend.database.session import SessionMaker  # type: ignore
            async with SessionMaker() as mem_sess:  # type: ignore
                mem_sess.add(
                    Memory(
                        tenant_id="tenant_default",
                        project_id=None,
                        kind="conversation",
                        tags={"auto_approved": auto_count, "pending": 0},
                        trace_id=ctx.trace_id,
                    )
                )
                for act in validated:
                    if act.action == AiActionType.report:
                        mem_sess.add(
                            Memory(
                                tenant_id="tenant_default",
                                project_id=None,
                                kind="design",
                                tags={"action": "report"},
                                trace_id=ctx.trace_id,
                            )
                        )
                await mem_sess.commit()
        except Exception:
            pass
        return validated

    @classmethod
    def dep(cls) -> "AiOrchestrator":
        """Return orchestrator instance for FastAPI dependency injection."""

        return cls()
