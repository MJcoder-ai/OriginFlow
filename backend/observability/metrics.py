from __future__ import annotations
import os
import time
from typing import Optional

METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() in ("1","true","yes")

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest
except Exception:  # pragma: no cover
    METRICS_ENABLED = False
    # Define no-op shims
    class _Noop:
        def labels(self, *_, **__): return self
        def inc(self, *_ , **__): return None
        def observe(self, *_ , **__): return None
        def set(self, *_ , **__): return None
    Counter = Histogram = Gauge = lambda *_, **__: _Noop()  # type: ignore
    CollectorRegistry = object  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    def generate_latest(*_, **__): return b""

# -------- Registry (use default global to play nice with multiprocess/uwsgi if needed) --------
REGISTRY: Optional[CollectorRegistry] = None

# -------- Metrics --------
policy_cache_get_latency = Histogram(
    "policy_cache_get_latency_seconds",
    "Latency for policy cache get()",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    labelnames=("backend","tenant_id"),
)
policy_cache_db_load_latency = Histogram(
    "policy_cache_db_load_latency_seconds",
    "Latency for DB load when cache miss",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    labelnames=("tenant_id",),
)
policy_cache_hits = Counter(
    "policy_cache_hits_total",
    "Number of policy cache hits",
    labelnames=("layer","tenant_id"),  # layer=memory|redis
)
policy_cache_misses = Counter(
    "policy_cache_misses_total",
    "Number of policy cache misses",
    labelnames=("layer","tenant_id"),  # layer=memory|redis|db
)
policy_cache_sets = Counter(
    "policy_cache_sets_total",
    "Times policy doc stored/updated in cache",
    labelnames=("backend","tenant_id"),  # backend=memory|redis
)
policy_cache_invalidations = Counter(
    "policy_cache_invalidations_total",
    "Cache invalidations",
    labelnames=("tenant_id",),
)
policy_cache_dogpile_wait = Counter(
    "policy_cache_dogpile_wait_total",
    "Dogpile lock waits on cache miss",
    labelnames=("tenant_id",),
)

# ---------------------------------------------------------------------------
# HTTP server metrics
# ---------------------------------------------------------------------------
try:
    http_requests_total  # type: ignore[name-defined]
except NameError:  # pragma: no cover - module import guard
    # Cardinality note:
    #  - route uses templated path (e.g., /api/v1/foo/{id}) to keep label space bounded
    #  - tenant_id keeps multi-tenant visibility; use "unknown" if not set
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        labelnames=("method", "route", "code", "tenant_id"),
    )

try:
    http_request_duration_seconds  # type: ignore[name-defined]
except NameError:  # pragma: no cover - module import guard
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        labelnames=("method", "route", "code", "tenant_id"),
        # Sane buckets for API traffic
        buckets=(
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
        ),
    )

try:
    http_requests_in_flight  # type: ignore[name-defined]
except NameError:  # pragma: no cover - module import guard
    http_requests_in_flight = Gauge(
        "http_requests_in_flight",
        "HTTP requests currently in flight",
        labelnames=("method", "route", "tenant_id"),
    )

# ---------------------------------------------------------------------------
# HTTP payload sizes & exceptions
# ---------------------------------------------------------------------------
try:
    http_request_size_bytes  # type: ignore[name-defined]
except NameError:
    http_request_size_bytes = Histogram(
        "http_request_size_bytes",
        "HTTP request size in bytes",
        labelnames=("method", "route", "code", "tenant_id"),
        buckets=(
            256,
            1024,
            4096,
            16384,
            65536,
            262144,
            1048576,
            4194304,
            16777216,
        ),
    )

try:
    http_response_size_bytes  # type: ignore[name-defined]
except NameError:
    http_response_size_bytes = Histogram(
        "http_response_size_bytes",
        "HTTP response size in bytes",
        labelnames=("method", "route", "code", "tenant_id"),
        buckets=(
            256,
            1024,
            4096,
            16384,
            65536,
            262144,
            1048576,
            4194304,
            16777216,
        ),
    )

try:
    http_exceptions_total  # type: ignore[name-defined]
except NameError:
    http_exceptions_total = Counter(
        "http_exceptions_total",
        "Total ASGI exceptions during request handling",
        labelnames=("exception", "method", "route", "tenant_id"),
    )

approval_decisions = Counter(
    "approval_decisions_total",
    "Approval decision outcomes",
    labelnames=("result","reason","action_type","agent_name","tenant_id"),
)
approval_decision_latency = Histogram(
    "approval_decision_latency_seconds",
    "Latency of computing approval decision",
    buckets=(0.001,0.005,0.01,0.025,0.05,0.1,0.25,0.5),
    labelnames=("tenant_id",),
)
approvals_enqueued = Counter(
    "approvals_enqueued_total",
    "Actions enqueued for manual approval",
    labelnames=("reason","action_type","tenant_id"),
)
analyze_actions_processed = Counter(
    "analyze_actions_processed_total",
    "Actions processed by analyze_service",
    labelnames=("tenant_id",),
)
analyze_process_latency = Histogram(
    "analyze_process_latency_seconds",
    "Latency for analyze_service.process",
    buckets=(0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2),
    labelnames=("tenant_id",),
)

def now() -> float:
    return time.perf_counter()

