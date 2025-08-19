import re
import importlib.util
from pathlib import Path

from fastapi import FastAPI, Response, HTTPException
from fastapi.testclient import TestClient

from backend.middleware.http_metrics import HTTPMetricsMiddleware
from backend.observability.metrics import (
    METRICS_ENABLED,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


# Load test-only routes without importing heavy packages
spec = importlib.util.spec_from_file_location(
    "backend.api.routes.test_only",
    Path(__file__).resolve().parents[2] / "backend/api/routes/test_only.py",
)
test_only = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_only)  # type: ignore[arg-type]


app = FastAPI()
app.add_middleware(HTTPMetricsMiddleware)
app.include_router(test_only.router, prefix="/__test__")


@app.get("/metrics")
async def metrics_endpoint():
    if not METRICS_ENABLED:
        raise HTTPException(status_code=503, detail="Metrics disabled")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


client = TestClient(app)


def _scrape_metric(body: bytes, name: str, labels: dict[str, str]) -> float:
    """Return metric value matching labels (order agnostic)."""
    text = body.decode("utf-8")
    pattern = re.compile(rf'^{re.escape(name)}\{{([^}}]*)\}}\s+([0-9\.eE+-]+)$', re.MULTILINE)
    for lbls, val in pattern.findall(text):
        parsed = {}
        for item in lbls.split(","):
            k, _, v = item.partition("=")
            parsed[k] = v.strip('"')
        if all(parsed.get(k) == v for k, v in labels.items()):
            return float(val)
    return 0.0


def test_http_metrics_success_and_error_paths():
    before = client.get("/metrics")
    assert before.status_code == 200

    r1 = client.get("/__test__/ok")
    assert r1.status_code == 200
    r2 = client.get("/__test__/boom")
    assert r2.status_code == 500

    after = client.get("/metrics")
    assert after.status_code == 200

    ok_metric = {"method": "GET", "route": "/__test__/ok", "code": "200", "tenant_id": "unknown"}
    boom_metric = {"method": "GET", "route": "/__test__/boom", "code": "500", "tenant_id": "unknown"}
    assert _scrape_metric(after.content, "http_requests_total", ok_metric) >= _scrape_metric(before.content, "http_requests_total", ok_metric) + 1
    assert _scrape_metric(after.content, "http_requests_total", boom_metric) >= _scrape_metric(before.content, "http_requests_total", boom_metric) + 1

    assert re.search(r'http_request_duration_seconds_bucket\{[^}]*route="/__test__/ok"', after.text)
    assert re.search(r'http_request_duration_seconds_bucket\{[^}]*route="/__test__/boom"', after.text)

