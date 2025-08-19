from __future__ import annotations
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.observability.request_context import set_request_id

class LogContextMiddleware(BaseHTTPMiddleware):
    """
    Ensures request_id is present in a contextvar for logging correlation.
    - Reads X-Request-ID if provided; otherwise generates a short UUID.
    - Always sets response header X-Request-ID.
    Safe to run alongside any existing request id middleware (no conflicts).
    """
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        set_request_id(rid)
        response: Response = await call_next(request)
        response.headers.setdefault("X-Request-ID", rid)
        return response
