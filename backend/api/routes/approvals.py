"""
Approvals API

Endpoints:
- POST /approvals/propose         → store a proposed patch for review
- POST /approvals/{id}/decision  → approve/reject; approval applies patch on approve
- GET  /approvals?session_id=... → list proposals for a session
"""
from __future__ import annotations

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from sqlalchemy import select
from backend.db.session import get_db
from backend.governance.approvals import init_approvals, approvals, propose as _propose, decide as _decide

router = APIRouter(prefix="/approvals", tags=["Approvals"])


class ProposeRequest(BaseModel):
    approval_id: str = Field(..., description="Client-generated idempotent id")
    session_id: str
    task: str
    request_id: str
    patch_json: Dict


@router.post("/propose")
def propose(req: ProposeRequest, db: Session = Depends(get_db)):
    init_approvals(db)
    return _propose(
        db,
        approval_id=req.approval_id,
        session_id=req.session_id,
        task=req.task,
        request_id=req.request_id,
        patch_json=req.patch_json,
    )


class DecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")


@router.post("/{approval_id}/decision")
def decision(approval_id: str, req: DecisionRequest, db: Session = Depends(get_db)):
    try:
        rec, version = _decide(db, approval_id=approval_id, decision=req.decision)
        return {"record": rec, "applied_version": version}
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("")
def list_approvals(session_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    init_approvals(db)
    stmt = select(approvals)
    if session_id:
        stmt = stmt.where(approvals.c.session_id == session_id)
    rows = db.execute(stmt).fetchall()
    return [dict(r._mapping) for r in rows]
