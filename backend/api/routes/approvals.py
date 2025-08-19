from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_session
from backend.auth.dependencies import require_permission
from backend.schemas.approvals import ApprovalDecision, BatchDecisionRequest
from backend.services.approval_queue_service import ApprovalQueueService


router = APIRouter(prefix="/api/v1/approvals", tags=["Approvals"])


@router.get("/", dependencies=[Depends(require_permission("approvals.read"))])
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
    await session.commit()
    # Return payload so client can apply via existing /act endpoint
    return {"approved": row.to_dict(), "apply_client_side": True}


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
    return {"rejected": row.to_dict()}


@router.post("/batch", dependencies=[Depends(require_permission("approvals.approve"))])
async def batch_decide(
    body: BatchDecisionRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None) or "default"
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
                results.append({"id": item.id, "status": "approved"})
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
    return {"results": results}

