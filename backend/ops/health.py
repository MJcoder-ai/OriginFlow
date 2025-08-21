from __future__ import annotations

import os
import platform
import time
from typing import Any, Dict

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/healthz")
async def healthz() -> Dict[str, Any]:
    """Liveness probe with basic process info."""
    return {
        "status": "ok",
        "time": time.time(),
        "pid": os.getpid(),
        "python": platform.python_version(),
    }


@router.get("/info")
async def info(request: Request) -> Dict[str, Any]:
    """
    Operational info useful for debugging and dashboards.
    Never include secrets here; this is safe to expose internally.
    """
    return {
        "service": "originflow-backend",
        "env": os.getenv("APP_ENV", "dev"),
        "git_sha": os.getenv("GIT_SHA", "unknown"),
        "ai_ready": bool(getattr(request.app.state, "ai_ready", False)),
        "request_id": getattr(
            getattr(request, "state", object()), "request_id", None
        ),
    }


@router.get("/readyz")
async def readyz(request: Request):
    """
    Readiness probe that checks AI initialization and database connectivity.
    Returns 503 if any dependency is not ready.
    """
    checks = {"ai": False, "db": False}
    details: Dict[str, Any] = {}

    # 1) AI readiness (flag set during startup)
    ai_ready = bool(getattr(request.app.state, "ai_ready", False))
    checks["ai"] = ai_ready
    if not ai_ready:
        details["ai"] = "AI services not initialized"

    # 2) DB connectivity (works for SQLite + aiosqlite, and other drivers)
    try:
        # Single source of truth for async engine
        from backend.database.session import async_engine  # type: ignore
        async with async_engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        checks["db"] = True
    except Exception as ex:
        checks["db"] = False
        details["db"] = f"DB not ready: {ex.__class__.__name__}"

    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "not_ready", "checks": checks, "details": details},
    )
