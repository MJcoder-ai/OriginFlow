from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Any

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
    async def enqueue_from_action(
        session: AsyncSession,
        tenant_id: str,
        action_obj: Any,
        reason: str,
        confidence: Optional[float] = None,
    ) -> PendingAction:
        """Persist a ``PendingAction`` from a heterogeneous object."""
        action_type = getattr(action_obj, "action", None) or getattr(action_obj, "action_type", None)
        agent_name = getattr(action_obj, "_agent_name", None) or getattr(action_obj, "agent_name", None)
        session_id = getattr(action_obj, "session_id", None)
        project_id = getattr(action_obj, "project_id", None)
        payload = getattr(action_obj, "payload", None)
        if isinstance(action_obj, dict):
            action_type = action_type or action_obj.get("action") or action_obj.get("action_type")
            agent_name = agent_name or action_obj.get("agent_name")
            session_id = session_id or action_obj.get("session_id")
            project_id = project_id or action_obj.get("project_id")
            payload = payload or action_obj.get("payload")
            confidence = confidence if confidence is not None else action_obj.get("confidence")
        pa = PendingAction(
            tenant_id=tenant_id,
            project_id=project_id,
            session_id=session_id,
            agent_name=agent_name,
            action_type=action_type,
            payload=payload,
            confidence=confidence,
            status="pending",
            reason=reason,
        )
        session.add(pa)
        await session.flush()
        return pa

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

