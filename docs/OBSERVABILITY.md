# Observability: Metrics & Tracing

This patch adds **Prometheus** metrics and optional **OpenTelemetry** tracing across:
1) **Policy cache** (hits, misses, dogpile locks, latency)
2) **Approval decisions** (result, reason, action type, agent, latency)
3) **Analyze** pipeline (processed actions, enqueued approvals, latency)
4) **Agent registry** hydration counts by domain

## Enabling

Env vars:

| Var | Default | Description |
|---|---|---|
| `METRICS_ENABLED` | `true` | Toggle Prometheus metrics registry |
| `METRICS_PUBLIC` | `false` | If `true`, exposes `/metrics` without RBAC (use behind a private network) |
| `TRACING_ENABLED` | `false` | Enable OpenTelemetry tracing |
| `OTEL_SERVICE_NAME` | `originflow-backend` | Service name resource |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTLP HTTP endpoint (collector) |

## Endpoint

- `GET /metrics` — Prometheus plaintext.
  - If `METRICS_PUBLIC=false`, RBAC requires `metrics.read`.

## Key Metrics

- `policy_cache_hits_total{layer,tenant_id}` — Hits at `memory|redis`.
- `policy_cache_misses_total{layer,tenant_id}` — Misses at `memory|redis|db`.
- `policy_cache_get_latency_seconds{backend,tenant_id}` — Cache get latency; `backend=memory|redis|db`.
- `policy_cache_db_load_latency_seconds{tenant_id}` — DB fetch time on miss.
- `policy_cache_sets_total{backend,tenant_id}` — Cache set ops.
- `policy_cache_invalidations_total{tenant_id}` — Invalidations.
- `policy_cache_dogpile_wait_total{tenant_id}` — Lock waits on miss.

- `approval_decisions_total{result,reason,action_type,agent_name,tenant_id}` — `result=allow|deny`.
- `approval_decision_latency_seconds{tenant_id}` — decision latency.

- `analyze_actions_processed_total{tenant_id}` — processed actions.
- `analyze_process_latency_seconds{tenant_id}` — analyze latency.
- `approvals_enqueued_total{reason,action_type,tenant_id}` — queued approvals.

- `registry_agents_registered_total{domain,tenant_id}` — hydrated agents.

> ⚠️ **Cardinality**: `tenant_id`, `action_type`, `agent_name` increase series count. For large multi-tenant fleets, consider hashing or bucketing to limit cardinality.

## Tracing

Set `TRACING_ENABLED=true` and point `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector.
The app instruments FastAPI/Starlette automatically. Spans include approval decision points and can be correlated with logs via OTEL context.

## Log Correlation

Structured logging is initialized at startup (`backend/observability/logging.py`), adding:

- `trace_id`, `span_id`, `trace_sampled` (when tracing is enabled)  
- `tenant_id` (from context) and `request_id` (from `X-Request-ID`)  

See `docs/LOGGING.md` for env toggles and examples.

## Grafana Ideas

- **SLO**: p95 of `analyze_process_latency_seconds` < 250ms, alert on burn rate.
- **Auto-approval rate**: derived from `approval_decisions_total{result="allow"}` / total.
- **Cache efficiency**: hits/(hits+misses) by layer; alert if redis miss rate > 10%.
- **Queue health**: track `approvals_enqueued_total` rate; alert on spikes.

