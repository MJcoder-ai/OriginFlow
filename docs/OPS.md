# Ops Hardening (Phase 5)

This document describes operational endpoints, middleware and recommended run commands for production-like environments.

## Endpoints

- **Liveness**: `GET /api/v1/system/healthz` – always returns `{"status":"ok"}` with process info.
- **Readiness**: `GET /api/v1/system/readyz` – verifies DB connectivity and AI initialization.
- **Info**: `GET /api/v1/system/info` – returns non-sensitive runtime details.
- **Metrics**: `GET /api/v1/system/metrics` – JSON snapshot of in-process counters.

These are additive to the OriginFlow API surface. See also `docs/API_ENDPOINTS.md`.

## Request ID propagation

All requests receive/propagate `X-Request-ID`. Clients can set it; otherwise a UUID is generated. The value is echoed in responses and available to handlers via `request.state.request_id`.

## Running (production-style logs)

```bash
poetry run uvicorn backend.main:app \
  --host 0.0.0.0 --port 8000 \
  --log-config backend/logging.prod.json
```

## Quick checks

```bash
curl -s localhost:8000/api/v1/system/healthz | jq
curl -s localhost:8000/api/v1/system/readyz | jq
curl -s localhost:8000/api/v1/system/info | jq
curl -s localhost:8000/api/v1/system/metrics | jq
curl -s "http://localhost:8000/api/v1/odl/sessions/demo/text?layer=single-line" | jq
```

## CORS (dev)
The frontend sends `If-Match` when calling `POST /api/v1/ai/act`. Ensure the backend
allows this header during preflight. The default dev config enables common localhost
origins and permits `If-Match`, `X-Request-ID`, and `Content-Type`. You can override
origins with:

```
export ORIGINFLOW_CORS_ORIGINS="http://localhost:8082"
```

## Git hygiene for runtime stores

We ignore `.localdb/` and `qdrant_storage/` to avoid permission conflicts during `git pull` and to keep runtime data out of version control.

## Notes

- These features are intentionally **dependency-light**. If you later adopt Prometheus, you can replace `backend/ops/metrics.py` with a client exporter without touching call sites.
- Readiness depends on an `app.state.ai_ready` flag. The existing startup path already logs AI initialization; ensure it sets `app.state.ai_ready = True` when complete.

