from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pending_action import PendingAction


class ApprovalQueueService:
    """CRUD & state transitions for pending_actions."""

    @staticmethod
    async def enqueue(
        session: AsyncSession,
        *,
        tenant_id: str,
        action_type: str,
        payload: dict,
        confidence: Optional[float],
        project_id: Optional[str],
        session_id: Optional[str],
        agent_name: Optional[str],
        requested_by_id: Optional[str],
        reason: Optional[str] = None,
    ) -> PendingAction:
        row = PendingAction(
            tenant_id=tenant_id,
            project_id=project_id,
            session_id=session_id,
            agent_name=agent_name,
            action_type=action_type,
            payload=payload,
            confidence=confidence,
            status="pending",
            reason=reason,
            requested_by_id=requested_by_id,
        )
        session.add(row)
        await session.flush()
        return row

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        tenant_id: str,
        status: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PendingAction]:
        stmt = select(PendingAction).where(PendingAction.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(PendingAction.status == status)
        if session_id:
            stmt = stmt.where(PendingAction.session_id == session_id)
        if project_id:
            stmt = stmt.where(PendingAction.project_id == project_id)
        stmt = stmt.order_by(PendingAction.created_at.desc()).limit(limit).offset(offset)
        rows = (await session.execute(stmt)).scalars().all()
        return rows

    @staticmethod
    async def get(session: AsyncSession, *, id: int, tenant_id: str) -> Optional[PendingAction]:
        stmt = select(PendingAction).where(
            PendingAction.id == id, PendingAction.tenant_id == tenant_id
        )
        return await session.scalar(stmt)

    @staticmethod
    async def approve(
        session: AsyncSession,
        *,
        row: PendingAction,
        approver_id: Optional[str],
        note: Optional[str],
    ) -> PendingAction:
        row.status = "approved"
        row.reason = note
        row.approved_by_id = approver_id
        row.updated_at = datetime.utcnow()
        return row

    @staticmethod
    async def reject(
        session: AsyncSession,
        *,
        row: PendingAction,
        approver_id: Optional[str],
        note: Optional[str],
    ) -> PendingAction:
        row.status = "rejected"
        row.reason = note
        row.approved_by_id = approver_id
        row.updated_at = datetime.utcnow()
        return row

    @staticmethod
    async def mark_applied(session: AsyncSession, *, row: PendingAction) -> PendingAction:
        row.status = "applied"
        row.applied_at = datetime.utcnow()
        row.updated_at = row.applied_at
        return row

