from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.database.session import get_session
from backend.auth.dependencies import require_permission
from backend.api.deps_tenant import seed_tenant_context
from backend.schemas.approvals import ApprovalDecision, BatchDecisionRequest
from backend.services.approval_queue_service import ApprovalQueueService
from backend.services.approvals_events import ApprovalsEventBus
from backend.orchestrator.orchestrator import Orchestrator
from backend.orchestrator.router import ActArgs
from starlette.responses import StreamingResponse
import asyncio
import json
from backend.services.impact_preview_service import ImpactPreviewService


router = APIRouter(prefix="/api/v1/approvals", tags=["Approvals"])

@router.get("/stream", dependencies=[Depends(require_permission("approvals.read"))])
async def stream_approvals(
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user),
):
    """Server-Sent Events (SSE) stream of approval updates for the caller's tenant.
    Events: pending.created | pending.updated | pending.approved | pending.rejected | pending.applied | heartbeat
    """
    tenant_id = getattr(user, "tenant_id", None) or "default"
    q = ApprovalsEventBus.subscribe(tenant_id)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'hello', 'tenant_id': tenant_id})}\n\n"
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(item)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            ApprovalsEventBus.unsubscribe(tenant_id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{id}/diff", dependencies=[Depends(require_permission("approvals.read"))])
async def get_diff(
    id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    """Return a preview diff for the specified pending action."""

    tenant_id = getattr(user, "tenant_id", None) or "default"
    try:
        preview = await ImpactPreviewService.build_preview(
            session, pending_id=id, tenant_id=tenant_id
        )
        return preview
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pending action not found"
        )
    except Exception as e:  # pragma: no cover - defensive fallback
        return {
            "error": str(e),
            "before_snapshot": None,
            "after_preview": {
                "graph": {"nodes": [], "edges": []},
                "note": "Preview unavailable due to server error",
            },
            "diff": {
                "added_nodes": [],
                "removed_nodes": [],
                "modified_nodes": [],
                "added_edges": [],
                "removed_edges": [],
            },
        }

@router.get("/", dependencies=[Depends(require_permission("approvals.read")), Depends(seed_tenant_context)])
async def list_pending(
    status: Optional[str] = None,
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None) or "default"
    rows = await ApprovalQueueService.list(
        session,
        tenant_id=tenant_id,
        status=status,
        session_id=session_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return {"items": [r.to_dict() for r in rows]}


@router.post("/{id}/approve", dependencies=[Depends(require_permission("approvals.approve"))])
async def approve_one(
    id: int,
    body: ApprovalDecision,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None) or "default"
    row = await ApprovalQueueService.get(session, id=id, tenant_id=tenant_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if row.status not in ("pending", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not approvable from state {row.status}",
        )
    await ApprovalQueueService.approve(
        session, row=row, approver_id=getattr(user, "id", None), note=body.note
    )
    apply_result = None
    orch = Orchestrator()
    if body.approve_and_apply:
        if row.status == "applied":
            await session.commit()
            return {"approved": row.to_dict(), "already_applied": True}
        action = {"type": row.action_type, "payload": {**(row.payload or {})}}
        if row.session_id and "session_id" not in action["payload"]:
            action["payload"]["session_id"] = row.session_id
        act_args = ActArgs(layer="single-line", attrs=action["payload"])
        try:
            result = await orch.run(
                db=session,
                session_id=row.session_id,
                task=action["type"],
                request_id=f"approval-{id}",
                args=act_args,
            )
            apply_result = result
            if result and result.get("status") == "complete" and result.get("patch"):
                await ApprovalQueueService.mark_applied(session, row=row)
        except Exception as e:  # pragma: no cover - defensive
            await session.commit()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Apply failed: {e}")
    await session.commit()
    try:
        if body.approve_and_apply and row.status == "applied":
            ApprovalsEventBus.publish_applied(tenant_id, row.to_dict())
        else:
            ApprovalsEventBus.publish_approved(tenant_id, row.to_dict())
    except (ConnectionError, AttributeError, KeyError) as e:
        # Event bus publishing failed - log but don't fail the approval
        import logging
        logger = logging.getLogger("backend.api.approvals")
        logger.warning("Failed to publish approval event: %s", e)
    return {
        "approved": row.to_dict(),
        "apply_client_side": not body.approve_and_apply,
        "server_apply_result": apply_result,
    }


@router.post("/{id}/reject", dependencies=[Depends(require_permission("approvals.approve"))])
async def reject_one(
    id: int,
    body: ApprovalDecision,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None) or "default"
    row = await ApprovalQueueService.get(session, id=id, tenant_id=tenant_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if row.status not in ("pending", "approved"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not rejectable from state {row.status}",
        )
    await ApprovalQueueService.reject(
        session, row=row, approver_id=getattr(user, "id", None), note=body.note
    )
    await session.commit()
    try:
        ApprovalsEventBus.publish_rejected(tenant_id, row.to_dict())
    except (ConnectionError, AttributeError, KeyError) as e:
        # Event bus publishing failed - log but don't fail the rejection
        import logging
        logger = logging.getLogger("backend.api.approvals")
        logger.warning("Failed to publish rejection event: %s", e)
    return {"rejected": row.to_dict()}


@router.post("/batch", dependencies=[Depends(require_permission("approvals.approve"))])
async def batch_decide(
    body: BatchDecisionRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None) or "default"
    orch = Orchestrator()
    results = []
    for item in body.items:
        row = await ApprovalQueueService.get(session, id=item.id, tenant_id=tenant_id)
        if not row:
            results.append({"id": item.id, "error": "not_found"})
            continue
        try:
            if item.approve:
                await ApprovalQueueService.approve(
                    session,
                    row=row,
                    approver_id=getattr(user, "id", None),
                    note=item.note,
                )
                server_apply_result = None
                if item.approve_and_apply and row.status != "applied":
                    action = {"type": row.action_type, "payload": {**(row.payload or {})}}
                    if row.session_id and "session_id" not in action["payload"]:
                        action["payload"]["session_id"] = row.session_id
                    act_args = ActArgs(layer="single-line", attrs=action["payload"])
                    result = await orch.run(
                        db=session,
                        session_id=row.session_id,
                        task=action["type"],
                        request_id=f"approval-{item.id}",
                        args=act_args,
                    )
                    server_apply_result = result
                    if result and result.get("status") == "complete" and result.get("patch"):
                        await ApprovalQueueService.mark_applied(session, row=row)
                results.append({"id": item.id, "status": row.status, "server_apply_result": server_apply_result})
            else:
                await ApprovalQueueService.reject(
                    session,
                    row=row,
                    approver_id=getattr(user, "id", None),
                    note=item.note,
                )
                results.append({"id": item.id, "status": "rejected"})
        except Exception as e:  # pragma: no cover - best effort
            results.append({"id": item.id, "error": str(e)})
    await session.commit()
    try:
        for r in results:
            if "error" in r:
                continue
            row = await ApprovalQueueService.get(session, id=r["id"], tenant_id=tenant_id)
            if not row:
                continue
            if row.status == "applied":
                ApprovalsEventBus.publish_applied(tenant_id, row.to_dict())
            elif row.status == "approved":
                ApprovalsEventBus.publish_approved(tenant_id, row.to_dict())
            elif row.status == "rejected":
                ApprovalsEventBus.publish_rejected(tenant_id, row.to_dict())
    except (ConnectionError, AttributeError, KeyError) as e:
        # Event bus publishing failed - log but don't fail the batch operation
        import logging
        logger = logging.getLogger("backend.api.approvals")
        logger.warning("Failed to publish batch approval events: %s", e)
    return {"results": results}

