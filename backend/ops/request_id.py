from __future__ import annotations

import uuid
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_HDR = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach or propagate a correlation ID for each request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        req_id = request.headers.get(_HDR, str(uuid.uuid4()))
        # Expose in app.state for downstream handlers if needed
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers.setdefault(_HDR, req_id)
        return response
