"""
Approval workflow: proposals and decisions.

Approvals are stored in a simple table with status. An approval proposes a patch
for a session. Approving applies the patch via ODL with CAS at the current
version. Rejection records an audit event and leaves ODL unchanged.
"""
from __future__ import annotations

from typing import Dict, Tuple
from datetime import datetime, timezone
import asyncio
from sqlalchemy import Table, Column, String, JSON, MetaData, DateTime, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.odl.store import ODLStore
from backend.database.session import SessionMaker
from backend.audit.events import init_audit, log_event

metadata = MetaData()

approvals = Table(
    "approvals",
    metadata,
    Column("id", String, primary_key=True),
    Column("session_id", String, nullable=False),
    Column("task", String, nullable=False),
    Column("request_id", String, nullable=False),
    Column("patch_json", JSON, nullable=False),
    Column("status", String, nullable=False),  # proposed | approved | rejected
    Column("created_at", DateTime, nullable=False),
    Column("decided_at", DateTime, nullable=True),
)


def init_approvals(db: Session) -> None:
    engine = db.get_bind()
    metadata.create_all(engine)


def propose(
    db: Session,
    *,
    approval_id: str,
    session_id: str,
    task: str,
    request_id: str,
    patch_json: Dict,
) -> Dict:
    now = datetime.now(timezone.utc)
    try:
        db.execute(
            insert(approvals).values(
                id=approval_id,
                session_id=session_id,
                task=task,
                request_id=request_id,
                patch_json=patch_json,
                status="proposed",
                created_at=now,
            )
        )
        db.commit()
    except IntegrityError:
        rec = db.execute(select(approvals).where(approvals.c.id == approval_id)).fetchone()
        return {"id": approval_id, "status": rec._mapping["status"] if rec else "proposed"}
    init_audit(db)
    log_event(
        db,
        id=f"audit:{approval_id}:proposed",
        session_id=session_id,
        type="patch_proposed",
        payload={"approval_id": approval_id, "task": task, "request_id": request_id},
    )
    return {"id": approval_id, "status": "proposed"}


def decide(
    db: Session,
    *,
    approval_id: str,
    decision: str,
) -> Tuple[Dict, int | None]:
    row = db.execute(select(approvals).where(approvals.c.id == approval_id)).fetchone()
    if not row:
        raise KeyError("Approval not found")
    rec = dict(row._mapping)
    session_id = rec["session_id"]
    patch_json = rec["patch_json"]

    now = datetime.now(timezone.utc)
    if decision == "approve":
        # Apply patch with current version using async ODL store
        async def _apply() -> int:
            async with SessionMaker() as adb:
                store = ODLStore()
                from backend.odl.store import graphs
                from backend.odl.schemas import ODLPatch, ODLGraph
                res = await adb.execute(select(graphs).where(graphs.c.session_id == session_id))
                row = res.fetchone()
                if not row:
                    raise KeyError("Session not found")
                data = dict(row._mapping["graph_json"])
                actual_version = row._mapping["version"]
                if data.get("version") != actual_version:
                    data["version"] = actual_version
                    await adb.execute(
                        update(graphs).where(graphs.c.session_id == session_id).values(graph_json=data)
                    )
                    await adb.commit()
                g = ODLGraph.model_validate(data)
                patch = ODLPatch.model_validate(patch_json)
                _, new_version = await store.apply_patch_cas(adb, session_id, actual_version, patch)
                return new_version

        new_version = asyncio.run(_apply())
        db.execute(
            update(approvals).where(approvals.c.id == approval_id).values(
                {"status": "approved", "decided_at": now}
            )
        )
        db.commit()
        log_event(
            db,
            id=f"audit:{approval_id}:approved",
            session_id=session_id,
            type="patch_approved",
            payload={"approval_id": approval_id, "version": new_version},
        )
        log_event(
            db,
            id=f"audit:{approval_id}:applied",
            session_id=session_id,
            type="patch_applied",
            payload={"approval_id": approval_id, "version": new_version},
        )
        return {"id": approval_id, "status": "approved"}, new_version
    else:
        db.execute(
            update(approvals).where(approvals.c.id == approval_id).values(
                {"status": "rejected", "decided_at": now}
            )
        )
        db.commit()
        log_event(
            db,
            id=f"audit:{approval_id}:rejected",
            session_id=session_id,
            type="patch_rejected",
            payload={"approval_id": approval_id},
        )
        return {"id": approval_id, "status": "rejected"}, None
