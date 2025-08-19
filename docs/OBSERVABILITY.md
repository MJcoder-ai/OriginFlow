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

## HTTP Server Metrics

The `HTTPMetricsMiddleware` records per-request metrics with bounded
cardinality using the route template and tenant ID:

- `http_requests_total{method,route,code,tenant_id}`
- `http_request_duration_seconds_bucket{method,route,code,tenant_id}`
- `http_requests_in_flight{method,route,tenant_id}`
- `http_request_size_bytes_bucket{method,route,code,tenant_id}` (+ `_sum`, `_count`)
- `http_response_size_bytes_bucket{method,route,code,tenant_id}` (+ `_sum`, `_count`)
- `http_exceptions_total{exception,method,route,tenant_id}`

If tenant context is unset, `tenant_id` defaults to `"unknown"`.

### 5xx Alert

`infra/k8s/monitoring/prometheusrule-originflow.yaml` enables alert
`Backend5xxRateHigh` when the proportion of 5xx responses exceeds 2% for
15 minutes (per tenant):

```promql
sum by (tenant_id) (rate(http_requests_total{code=~"5.."}[5m])) /
clamp_min(sum by (tenant_id) (rate(http_requests_total[5m])), 1) > 0.02
```

### Useful PromQL

**Avg request size (last 5m) by route**
```promql
sum by (route) (rate(http_request_size_bytes_sum[5m])) /
clamp_min(sum by (route) (rate(http_request_size_bytes_count[5m])), 1)
```

**Exception rate by class (5m)**
```promql
sum by (exception) (rate(http_exceptions_total[5m]))
```

**Top routes by response size (5m)**
```promql
topk(5, sum by (route) (rate(http_response_size_bytes_sum[5m])))
```

### Recorded Series (use these to reduce dashboard load)
We precompute common aggregations at 5m & 1h windows:

- HTTP latency p95

  `http_request_duration_seconds:p95_5m_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

  `http_request_duration_seconds:p95_1h_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`
- Analyze latency p95

  `analyze_process_latency_seconds:p95_5m_by_tenant{tenant_id=~"$tenant"}`

  `analyze_process_latency_seconds:p95_1h_by_tenant{tenant_id=~"$tenant"}`
- Average sizes

  Requests: `http_request_size_bytes:avg_5m_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

  Responses: `http_response_size_bytes:avg_5m_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

  Requests (1h): `http_request_size_bytes:avg_1h_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

  Responses (1h): `http_response_size_bytes:avg_1h_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`
- Size p95

  Requests: `http_request_size_bytes:p95_5m_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

  Responses: `http_response_size_bytes:p95_5m_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

  Requests (1h): `http_request_size_bytes:p95_1h_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

  Responses (1h): `http_response_size_bytes:p95_1h_by_route_tenant{tenant_id=~"$tenant", route=~"$route"}`

> Tip: You can swap existing dashboard queries to these recorded series for faster loads, especially on large time ranges.

## Dashboards & Alerts

### Dashboards
Import these JSON files into Grafana (Dashboards → New → Import):

- `infra/grafana/dashboards/originflow-policy-approvals.json`
- `infra/grafana/dashboards/originflow-slo.json`
- `infra/grafana/dashboards/originflow-http.json`  ← sizes & exceptions

Set the Prometheus datasource variable (`DS_PROMETHEUS`) during import if prompted.

### Alerts
Add/merge the Prometheus rules file into your Prometheus/Alertmanager deployment:

- `infra/prometheus/rules/originflow.rules.yml`

This defines:
- **AnalyzeLatencyHighShort/Long**: p95 analyze latency breach (short & long windows)
- **PolicyCacheRedisMissRateHigh**: redis miss rate > 30% for 30m
- **PolicyCacheDBFallbackRateHigh**: frequent DB fallbacks
- **ApprovalsEnqueueSpike**: rapid growth in manual approvals queue
- **Backend5xxRateHigh**: 5xx error rate > 2%

### E2E Tests

Run:
```bash
poetry run pytest -q tests/e2e/test_http_metrics.py
poetry run pytest -q tests/e2e/test_http_sizes_and_exceptions.py
poetry run pytest -q tests/e2e/test_metrics_and_decisions.py
```
These tests verify that:
- Policy cache metrics increment on **memory/redis hits** and **DB miss/dogpile**
- Approval decision metrics increment for **allow/deny** paths
- HTTP metrics export request counters and latency histograms
- Request/response size histograms and exception counters increment
- `/metrics` endpoint returns Prometheus exposition format

