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
    http_request_size_bytes,
    http_response_size_bytes,
    http_exceptions_total,
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
    * http_request_size_bytes_bucket{method, route, code, tenant_id}
    * http_response_size_bytes_bucket{method, route, code, tenant_id}
    * http_exceptions_total{exception, method, route, tenant_id}

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

        http_requests_in_flight.labels(method=method, route=route, tenant_id=tenant).inc()
        start = time.perf_counter()
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR

        # Determine request size
        req_size = 0
        try:
            cl = request.headers.get("content-length")
            if cl and cl.isdigit():
                req_size = int(cl)
            else:
                body = await request.body()
                req_size = len(body or b"")
        except Exception:
            req_size = 0

        try:
            response: Response = await call_next(request)
            status_code = int(getattr(response, "status_code", HTTP_500_INTERNAL_SERVER_ERROR))
            return response
        except BaseException as e:  # noqa: BLE001
            try:
                http_exceptions_total.labels(
                    exception=e.__class__.__name__,
                    method=method,
                    route=route,
                    tenant_id=tenant,
                ).inc()
            except Exception:
                pass
            raise
        finally:
            # Determine response size
            resp_size = 0
            try:
                if "response" in locals() and response is not None:  # type: ignore[name-defined]
                    cl = response.headers.get("content-length")
                    if cl and cl.isdigit():
                        resp_size = int(cl)
                    else:
                        body_bytes = getattr(response, "body", None)
                        if isinstance(body_bytes, (bytes, bytearray)):
                            resp_size = len(body_bytes)
            except Exception:
                resp_size = 0

            elapsed = time.perf_counter() - start
            http_request_duration_seconds.labels(
                method=method, route=route, code=str(status_code), tenant_id=tenant
            ).observe(elapsed)
            http_requests_total.labels(
                method=method, route=route, code=str(status_code), tenant_id=tenant
            ).inc()
            try:
                http_request_size_bytes.labels(
                    method=method, route=route, code=str(status_code), tenant_id=tenant
                ).observe(float(req_size))
                http_response_size_bytes.labels(
                    method=method, route=route, code=str(status_code), tenant_id=tenant
                ).observe(float(resp_size))
            except Exception:
                pass
            http_requests_in_flight.labels(
                method=method, route=route, tenant_id=tenant
            ).dec()

