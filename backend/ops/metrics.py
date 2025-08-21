from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Dict

from fastapi import APIRouter

# Very small in-process metrics. This intentionally avoids adding new deps
# (e.g., Prometheus client) to keep Phase 5 non-breaking. You can swap this
# module with Prometheus later without changing call sites.

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@dataclass
class Counter:
    name: str
    help: str
    value: int = 0

    def inc(self, n: int = 1) -> None:
        self.value += n


class _Registry:
    def __init__(self) -> None:
        self.counters: Dict[str, Counter] = {}
        self.started_at = time.time()

    def counter(self, name: str, help: str) -> Counter:
        if name not in self.counters:
            self.counters[name] = Counter(name=name, help=help)
        return self.counters[name]

    def snapshot(self) -> Dict[str, Dict]:
        return {
            "started_at": self.started_at,
            "counters": {k: asdict(v) for k, v in self.counters.items()},
        }


REGISTRY = _Registry()

# Canonical counters we care about in vNext.
_ACT_CALLS = REGISTRY.counter(
    "ai_act_calls_total", "Total POST /api/v1/ai/act requests"
)
_SESS_CREATED = REGISTRY.counter(
    "sessions_created_total", "Total ODL sessions created"
)
_PLAN_REQ = REGISTRY.counter(
    "planner_requests_total", "Total planner invocations"
)


async def track_request(path: str, method: str, status: int) -> None:
    """Increment counters based on request path and method."""
    if path.startswith("/api/v1/ai/act") and method.upper() == "POST":
        _ACT_CALLS.inc()
    elif path.startswith("/api/v1/odl/sessions") and method.upper() == "POST":
        _SESS_CREATED.inc()
    elif (
        path.startswith("/api/v1/odl/sessions")
        and "/plan" in path
        and method.upper() == "GET"
    ):
        _PLAN_REQ.inc()


@router.get("/metrics")
async def metrics_json() -> Dict[str, Dict]:
    """Return a minimal JSON metrics snapshot."""
    return REGISTRY.snapshot()
