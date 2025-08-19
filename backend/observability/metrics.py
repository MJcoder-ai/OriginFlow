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

