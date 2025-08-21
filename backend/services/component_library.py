"""
Component library service (DB-backed).

The orchestrator may use this service to fetch candidate real components
when replacing placeholders. Tools remain DB-agnostic; only the orchestrator
and services talk to the database.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session


def find_by_categories(
    db: Session,
    categories: List[str],
    min_power: Optional[float] = None,
    limit: int = 50,
) -> List[Dict]:
    """
    Return a list of component dicts from `component_master` matching categories.
    Each dict includes: part_number, name, manufacturer, category, power, price.
    """
    try:
        from backend.models.component_master import ComponentMaster  # type: ignore
    except Exception:
        # If your project stores component master elsewhere, adjust this import.
        raise RuntimeError("ComponentMaster model not found")

    stmt = select(ComponentMaster).where(ComponentMaster.category.in_(categories))
    rows = db.execute(stmt).scalars().all()
    out: List[Dict] = []
    for r in rows:
        if min_power is not None:
            try:
                p = float(r.power or 0)
                if p < float(min_power):
                    continue
            except Exception:
                continue
        out.append(
            {
                "part_number": r.part_number,
                "name": r.name,
                "manufacturer": r.manufacturer,
                "category": r.category,
                "power": r.power,
                "price": r.price,
            }
        )
        if len(out) >= limit:
            break
    return out
