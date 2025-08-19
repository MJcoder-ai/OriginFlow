# Structured Logging & OTEL Correlation

This service emits **structured JSON logs** (by default) with:

- `trace_id`, `span_id`, `trace_sampled` — when OpenTelemetry tracing is active  
- `tenant_id` — from `backend.utils.tenant_context`  
- `request_id` — per-request context (propagated via `X-Request-ID`)  
- `service`, `logger`, `level`, `msg`, `ts`, and optional `exc_info`

## Enable / Configure

Environment variables:

| Var | Default | Description |
|---|---|---|
| `LOG_JSON` | `true` | Emit JSON logs if true; otherwise single-line console |
| `LOG_LEVEL` | `INFO` | Global log level (e.g. `DEBUG`, `INFO`, `WARN`) |
| `LOG_INCLUDE_OTEL` | `true` | Include OTEL trace/span IDs when present |
| `TRACING_ENABLED` | `false` | (From tracing patch) Enable OpenTelemetry tracing |
| `OTEL_SERVICE_NAME` | `originflow-backend` | Service name in logs and OTEL |

## Request correlation

`LogContextMiddleware` ensures each response includes `X-Request-ID` and the same value is present in logs as `request_id`.  
If the client supplies `X-Request-ID`, it’s honored; otherwise, a short UUID is generated.

## OTEL correlation

When `TRACING_ENABLED=true` and an OTEL collector is configured, the `LoggingInstrumentor` enriches log records with:

- `otelTraceID` → exported as `trace_id`  
- `otelSpanID` → exported as `span_id`  
- `otelTraceSampled`

These fields let you pivot from logs to distributed traces in your APM.

## Example JSON line

```json
{
  "ts": "2025-08-19T14:23:55.123Z",
  "level": "INFO",
  "logger": "backend.services.analyze_service",
  "msg": "Queued action for manual approval",
  "trace_id": "f13d1f5c1d42f0a04d7a8d202ac3b2d1",
  "span_id": "4a8bc1e2281fd4b2",
  "trace_sampled": true,
  "tenant_id": "acme-prod",
  "request_id": "e9c3a1f2b4c7"
}
```

## Shipping logs

The output is stdout-friendly. To centralize:

- **Grafana Loki/ELK**: scrape container stdout  
- **GCP/AWS**: Cloud Logging/CloudWatch agents pick up stdout automatically

No additional dependency is required.
