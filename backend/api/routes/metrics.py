from __future__ import annotations
import os
from fastapi import APIRouter, Depends, Response, HTTPException, status
from backend.observability.metrics import METRICS_ENABLED, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional

router = APIRouter(prefix="/metrics", tags=["Observability"])

# Optional RBAC (default: private)
METRICS_PUBLIC = os.getenv("METRICS_PUBLIC", "false").lower() in ("1","true","yes")

try:
    from backend.api.deps import require_permission
except Exception:  # pragma: no cover
    def require_permission(_: str):
        async def _noop():
            return None
        return _noop

@router.get("")
async def metrics_endpoint(deps = Depends(require_permission("metrics.read")) if not METRICS_PUBLIC else None):
    if not METRICS_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Metrics disabled")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
