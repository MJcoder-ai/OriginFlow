from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pending_action import PendingAction


class ApprovalService:
    """Persist and manage pending AI actions awaiting approval."""

    @staticmethod
    async def queue(
        session: AsyncSession,
        *,
        tenant_id: str,
        project_id: Optional[str],
        session_id: Optional[str],
        trace_id: Optional[str],
        agent_name: str,
        action_type: str,
        risk_class: str,
        confidence: float,
        payload: dict,
        created_by: Optional[str] = None,
    ) -> PendingAction:
        pa = PendingAction(
            tenant_id=tenant_id,
            project_id=project_id,
            session_id=session_id,
            trace_id=trace_id,
            agent_name=agent_name,
            action_type=action_type,
            risk_class=risk_class,
            confidence=confidence,
            payload=payload,
            status="pending",
            created_by=created_by,
        )
        session.add(pa)
        await session.commit()
        await session.refresh(pa)
        return pa

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        tenant_id: str,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[PendingAction]:
        stmt = select(PendingAction).where(PendingAction.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(PendingAction.status == status)
        if project_id:
            stmt = stmt.where(PendingAction.project_id == project_id)
        stmt = stmt.order_by(PendingAction.created_at.desc()).limit(limit)
        rows = (await session.scalars(stmt)).all()
        return list(rows)

    @staticmethod
    async def decide(
        session: AsyncSession,
        *,
        pending_id: int,
        approved: bool,
        decided_by: str,
        reason: Optional[str] = None,
    ) -> PendingAction:
        row = await session.get(PendingAction, pending_id)
        if not row:
            raise ValueError(f"Pending action {pending_id} not found")
        if row.status != "pending":
            return row  # idempotent
        row.status = "approved" if approved else "rejected"
        row.decided_by = decided_by
        row.decision_reason = reason
        row.decided_at = datetime.utcnow()
        await session.commit()
        await session.refresh(row)
        return row

