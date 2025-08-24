from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional

PlanStatus = Literal["planned", "running", "completed", "blocked"]


@dataclass
class PlanTask:
    """One executable tool step in a LongPlan."""

    id: str
    title: str
    args: Dict[str, Any]
    layer: str = "single-line"
    can_auto: bool = True
    depends_on: List[str] = field(default_factory=list)
    risk: Literal["low", "medium", "high"] = "low"
    rationale: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LongPlan:
    """Full multi-step plan for a design request."""

    session_id: str
    layer: str
    tasks: List[PlanTask]
    status: PlanStatus = "planned"
    profile: Optional[str] = None
    notes: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "layer": self.layer,
            "status": self.status,
            "profile": self.profile,
            "notes": self.notes,
            "tasks": [t.as_dict() for t in self.tasks],
        }


@dataclass
class LongPlanCard:
    """Wrapper giving title + plan, suitable for ADPF card envelope."""

    title: str
    plan: LongPlan

    def as_card(self) -> Dict[str, Any]:
        return {"title": self.title, "plan": self.plan.as_dict()}
