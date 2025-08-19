from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from backend.observability.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_flight,
)
from backend.utils.tenant_context import get_tenant_id


def _route_template(request: Request) -> str:
    """
    Return the path template (e.g., '/api/v1/odl/sessions/{session_id}/act')
    if available; fall back to raw path when no template is known.
    """
    try:
        route = request.scope.get("route")
        if route and getattr(route, "path_format", None):  # FastAPI
            return route.path_format
        if route and getattr(route, "path", None):  # Starlette
            return route.path
    except Exception:  # pragma: no cover - defensive
        pass
    return request.url.path


class HTTPMetricsMiddleware(BaseHTTPMiddleware):
    """
    Record Prometheus metrics for every HTTP request:

    * http_requests_total{method, route, code, tenant_id}
    * http_request_duration_seconds_bucket{...}
    * http_requests_in_flight{method, route, tenant_id}

    Latencies are recorded even on exceptions; status code defaults to 500 on
    error. Metrics are best-effort and will noop if the Prometheus client is not
    available.
    """

    async def dispatch(self, request: Request, call_next):
        method = request.method
        route = _route_template(request)
        tenant = get_tenant_id()
        if not tenant or tenant == "default":
            tenant = "unknown"

        http_requests_in_flight.labels(
            method=method, route=route, tenant_id=tenant
        ).inc()
        start = time.perf_counter()
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR

        try:
            response: Response = await call_next(request)
            status_code = int(
                getattr(response, "status_code", HTTP_500_INTERNAL_SERVER_ERROR)
            )
            return response
        except BaseException:  # noqa: BLE001
            raise
        finally:
            elapsed = time.perf_counter() - start
            http_request_duration_seconds.labels(
                method=method, route=route, code=str(status_code), tenant_id=tenant
            ).observe(elapsed)
            http_requests_total.labels(
                method=method, route=route, code=str(status_code), tenant_id=tenant
            ).inc()
            http_requests_in_flight.labels(
                method=method, route=route, tenant_id=tenant
            ).dec()

