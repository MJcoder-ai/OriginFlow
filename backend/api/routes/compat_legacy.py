"""
Explicit 410 "Gone" responses for removed legacy endpoints.
This is *not* backward compatibility: it tells callers exactly what to use now.
Keeping this router mounted during the transition helps surface misconfigured clients.
Remove this file once all clients have migrated.
"""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


def _gone(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_410_GONE, detail=detail)


# --- Legacy AI analysis/plan endpoints ---------------------------------------
@router.post("/ai/analyze-design")
def analyze_design_removed() -> None:
    _gone("`POST /ai/analyze-design` has been removed. Use `POST /ai/act` instead.")


@router.get("/ai/plan")
def ai_plan_removed() -> None:
    _gone("`GET /ai/plan` has been removed. Implement a planner that emits `POST /ai/act` calls.")


# --- Legacy ODL session-scoped endpoints -------------------------------------
# Old shape: /odl/sessions/{session_id}/text
@router.get("/odl/sessions/{session_id}/text")
def odl_text_removed(session_id: str) -> None:  # pragma: no cover - simple 410
    _gone(
        "`GET /odl/sessions/{sid}/text` has been removed. Use `GET /odl/{sid}/view?layer=...` "
        "or add `/odl/{sid}/text` if you need a text serializer."
    )

