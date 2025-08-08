from __future__ import annotations
import uuid
from fastapi import Request
from starlette.responses import Response

async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = req_id
    response: Response = await call_next(request)
    response.headers["x-request-id"] = req_id
    return response
