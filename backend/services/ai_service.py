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
from uuid import uuid4
from pydantic import ValidationError
from backend.schemas.design_context import RequestContext, DesignSnapshot
from backend.policy.capabilities import ACTION_REQUIRED_SCOPES
from backend.services.ai_clients import get_openai_client
from backend.utils.logging import get_logger
from backend.utils.observability import trace_span, record_metric
from backend.services.approval_policy_service import ApprovalPolicyService
from backend.services.approval_queue_service import ApprovalQueueService

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
        *,
        tenant_id: str | None = None,
        project_id: str | None = None,
        session_id: str | None = None,
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
            AiActionType.wire: 0.5,
        }
        # Instrument validation and approval of raw AI actions
        with trace_span("ai_service.validate_actions", action_count=len(raw)):
            for action in raw:
                agent_name = action.pop("agent_name", "unknown")
                try:
                    obj = AiAction.model_validate(action)
                except Exception as exc:  # pragma: no cover - defensive
                    raise HTTPException(422, f"Invalid action schema: {exc}") from exc

                _check_capabilities(agent_name, obj)

                obj.confidence = _CONFIDENCE_MAP.get(obj.action, 0.5)

                if obj.action == AiActionType.add_component:
                    payload = obj.payload or {}
                    sc = payload.get("standard_code")
                    if not sc:
                        payload = {**payload, "standard_code": f"AUTO-{uuid4().hex[:8]}"}
                    try:
                        ComponentCreate(**payload)
                    except ValidationError as exc:
                        raise HTTPException(
                            status_code=422,
                            detail={"message": "Invalid component payload", "errors": exc.errors()},
                        ) from exc
                    obj.payload = payload
                elif obj.action == AiActionType.add_link:
                    LinkCreate(**obj.payload)
                elif obj.action == AiActionType.update_position:
                    PositionPayload(**obj.payload)
                elif obj.action == AiActionType.report:
                    BomReportPayload(**obj.payload)

                # store agent name for downstream approval queueing
                obj._agent_name = agent_name  # type: ignore[attr-defined]

                auto = False
                reason = None
                try:
                    from backend.database.session import SessionMaker  # type: ignore

                    async with SessionMaker() as _sess:
                        policy = await ApprovalPolicyService.for_tenant(
                            _sess, tenant_id or "tenant_default"
                        )
                        auto, reason, _, _ = await ApprovalPolicyService.is_auto_approved(
                            policy,
                            obj.action.value,
                            obj.confidence,
                            getattr(obj, "_agent_name", None),
                        )
                except Exception as e:  # pragma: no cover - policy failure fallback
                    logger.warning("Approval policy evaluation failed: %s", e)
                    auto, reason = False, str(e)

                obj.auto_approved = bool(auto)
                if not auto:
                    obj._approval_reason = reason  # type: ignore[attr-defined]
                else:
                    obj._approval_reason = reason  # retain info

                record_metric("action.processed", 1, {"agent": agent_name, "type": obj.action.value})
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

        # auto_count reflects the number of actions that passed risk-based
        # auto-approval.  Manual approvals will be needed for the remainder.
        auto_count = sum(
            1 for action in validated if getattr(action, "auto_approved", False)
        )
        # Record how many actions were auto approved vs total
        record_metric("action.auto_approved", auto_count, {"total": len(validated)})
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
                            "auto_approved": act.auto_approved,
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
            from backend.models.tenant_settings import TenantSettings  # noqa: F401
            from backend.models.pending_action import PendingAction  # noqa: F401

            async with SessionMaker() as mem_sess:  # type: ignore
                mem_sess.add(
                    Memory(
                        tenant_id=tenant_id or "tenant_default",
                        project_id=project_id,
                        kind="conversation",
                        tags={"auto_approved": auto_count, "pending": len(validated) - auto_count},
                        trace_id=ctx.trace_id,
                    )
                )
                for act in validated:
                    if act.action == AiActionType.report:
                        mem_sess.add(
                            Memory(
                                tenant_id=tenant_id or "tenant_default",
                                project_id=project_id,
                                kind="design",
                                tags={"action": "report"},
                                trace_id=ctx.trace_id,
                            )
                        )
                await mem_sess.commit()
        except Exception:
            pass

        # Queue non-auto-approved actions for manual approval
        try:
            from backend.database.session import SessionMaker  # type: ignore

            async with SessionMaker() as q_sess:
                queued_rows = []
                for act in validated:
                    if not getattr(act, "auto_approved", False):
                        row = await ApprovalQueueService.enqueue(
                            q_sess,
                            tenant_id=tenant_id or "tenant_default",
                            action_type=act.action.value,
                            payload=act.payload or {},
                            confidence=float(act.confidence or 0.0),
                            project_id=project_id,
                            session_id=session_id,
                            agent_name=getattr(act, "_agent_name", "unknown"),
                            requested_by_id=None,
                            reason=getattr(act, "_approval_reason", None),
                        )
                        queued_rows.append(row.to_dict())
                await q_sess.commit()

            # After commit, broadcast created events (no DB access needed).
            try:
                if queued_rows:
                    from backend.services.approvals_events import ApprovalsEventBus
                    for qi in queued_rows:
                        ApprovalsEventBus.publish_created(tenant_id or "tenant_default", qi)
            except Exception:
                pass
        except Exception:
            pass
        return validated

    async def apply_actions(
        self, actions: list[dict], *, context: dict | None = None
    ) -> list[dict]:
        """Execute a list of already-validated actions.

        Current architecture executes actions via dedicated endpoints. This
        placeholder simply returns the provided actions while allowing an
        optional context to be attached for downstream consumers. The method
        is asynchronous to mirror potential future executors.
        """

        try:  # Best-effort context attachment for future use
            if context is not None:
                setattr(self, "_apply_context", context)
        except Exception:  # pragma: no cover - defensive
            pass
        return actions

    @classmethod
    def dep(cls) -> "AiOrchestrator":
        """Return orchestrator instance for FastAPI dependency injection."""

        return cls()
