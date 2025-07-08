# backend/api/endpoints.py
"""API routes for OriginFlow.

Provides endpoints for CRUD operations on components and links.
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..models.data_models import Component, Link
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


@router.get("/components/{component_id}", response_model=schemas.Component)
def read_component(component_id: str, db: Session = Depends(get_db)) -> schemas.Component:
    """Return a single component by its ID."""

    db_component = db.query(Component).filter(Component.id == component_id).first()
    if db_component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return schemas.Component.model_validate(db_component)


@router.post("/links/", response_model=schemas.Link)
def create_link(link: schemas.LinkCreate, db: Session = Depends(get_db)) -> schemas.Link:
    """Create and persist a link between components."""

    db_link = Link(id=f"link_{uuid.uuid4()}", **link.model_dump())
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return schemas.Link.model_validate(db_link)


@router.get("/links/", response_model=List[schemas.Link])
def read_links(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[schemas.Link]:
    """Return a paginated list of links."""

    links = db.query(Link).offset(skip).limit(limit).all()
    return [schemas.Link.model_validate(l) for l in links]


@router.get("/links/{link_id}", response_model=schemas.Link)
def read_link(link_id: str, db: Session = Depends(get_db)) -> schemas.Link:
    """Return a single link by its ID."""

    db_link = db.query(Link).filter(Link.id == link_id).first()
    if db_link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return schemas.Link.model_validate(db_link)
