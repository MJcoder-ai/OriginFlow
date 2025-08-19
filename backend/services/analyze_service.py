from __future__ import annotations
import os

from openai import OpenAIError
import logging

from backend.services.ai_service import AiOrchestrator
from backend.schemas.ai import AnalyzeCommandRequest, AiAction, AiActionType
from backend.schemas.component import ComponentCreate
from backend.schemas.link import LinkCreate
from uuid import uuid4
from fastapi import HTTPException
from pydantic import ValidationError
from backend.utils.openai_helpers import map_openai_error
from backend.utils.observability import trace_span, record_metric
from backend.services.approval_policy_service import ApprovalPolicyService
from backend.services.approval_queue_service import ApprovalQueueService
from backend.utils.tenant_context import get_tenant_id
from backend.observability.metrics import (
    analyze_actions_processed,
    analyze_process_latency,
    approvals_enqueued,
    now,
)


logger = logging.getLogger(__name__)


class AnalyzeOrchestrator(AiOrchestrator):
    """Orchestrator aware of the design snapshot."""

    async def process(self, req: AnalyzeCommandRequest) -> list[AiAction]:
        prompt = self._serialize_snapshot(req)
        t0 = now()
        try:
            raw = await self.router_agent.handle(
                f"{prompt}\n\n{req.command}", snapshot=req.snapshot.model_dump()
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
        except ImportError as e:
            logger.warning(f"LearningAgent not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to assign confidence scores: {e}")

        tenant_id = get_tenant_id()
        try:
            from backend.database.session import SessionMaker  # type: ignore

            async with SessionMaker() as _sess:
                policy = await ApprovalPolicyService.for_tenant(_sess, tenant_id)
                with trace_span(
                    "analyze_service.auto_approval", action_count=len(actions)
                ):
                    for action in actions:
                        auto, reason, _, _ = await ApprovalPolicyService.is_auto_approved(
                            policy,
                            action.action.value,
                            action.confidence,
                            getattr(action, "_agent_name", None),
                        )
                        action.auto_approved = bool(auto)
                        if not auto:
                            action._approval_reason = reason  # type: ignore[attr-defined]
                        else:
                            action._approval_reason = reason
                        record_metric(
                            "action.auto_approved.decision",
                            1 if auto else 0,
                            {"type": action.action.value, "confidence": action.confidence},
                        )
        except Exception as e:
            logger.info(
                "Approval policy evaluation failed; routing all actions to manual review: %s",
                e,
            )
            for action in actions:
                action.auto_approved = False

        try:
            from backend.database.session import SessionMaker  # type: ignore

            async with SessionMaker() as q_sess:
                queued_rows = []
                for act in actions:
                    if not getattr(act, "auto_approved", False):
                        row = await ApprovalQueueService.enqueue_from_action(
                            q_sess,
                            tenant_id=tenant_id,
                            action_obj=act,
                            reason=getattr(act, "_approval_reason", None) or "",
                            confidence=act.confidence,
                        )
                        queued_rows.append(row.to_dict())
                        try:
                            approvals_enqueued.labels(
                                getattr(act, "_approval_reason", None) or "",
                                act.action.value,
                                tenant_id,
                            ).inc()
                        except Exception:
                            pass
                await q_sess.commit()
            try:
                if queued_rows:
                    from backend.services.approvals_events import ApprovalsEventBus

                    for qi in queued_rows:
                        ApprovalsEventBus.publish_created(tenant_id, qi)
            except Exception:
                pass
        except Exception:
            pass

        try:
            analyze_actions_processed.labels(tenant_id).inc(len(actions))
            analyze_process_latency.labels(tenant_id).observe(now() - t0)
        except Exception:
            pass
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
            agent_name = action.pop("agent_name", "unknown")
            obj = AiAction.model_validate(action)
            # Assign initial heuristic confidence score
            obj.confidence = _CONFIDENCE_MAP.get(obj.action, 0.5)
            obj._agent_name = agent_name  # type: ignore[attr-defined]
            
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
                        detail={
                            "message": "Invalid component payload",
                            "errors": exc.errors(),
                        },
                    ) from exc
                obj.payload = payload
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
