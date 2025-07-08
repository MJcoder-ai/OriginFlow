# backend/api/endpoints.py
"""API routes for OriginFlow.

Provides endpoints for CRUD operations on components.
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..models.data_models import Component
from ..database import get_db

router = APIRouter()

@router.post("/components/", response_model=schemas.Component)
def create_component(component: schemas.ComponentCreate, db: Session = Depends(get_db)) -> schemas.Component:
    """Create and persist a new component."""

    db_component = Component(id=f"component_{uuid.uuid4()}", **component.model_dump())
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    return schemas.Component.model_validate(db_component)

@router.get("/components/", response_model=List[schemas.Component])
def read_components(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[schemas.Component]:
    """Return a paginated list of components."""

    components = db.query(Component).offset(skip).limit(limit).all()
    return [schemas.Component.model_validate(c) for c in components]
