# Performance and Scaling

This document outlines recent enhancements that improve the
performance and observability of the OriginFlow backend.

## Metrics collection

A lightweight in-memory metrics service records counters and latency
measurements for various operations.  The service lives in
`backend/services/metrics_service.py` and exposes metrics through the
`/api/v1/metrics` endpoint.  Each latency metric is suffixed with
`_avg` and reported in seconds.

Operations currently instrumented:

- Compatibility validation
- Snapshot saving, listing, retrieval and diffing

## Caching

The `CompatibilityEngine` caches validation results keyed by
`(session_id, version)`.  Revalidating an unchanged snapshot returns
the cached report, avoiding redundant computation.

## Future scaling considerations

For production deployments, consider replacing the in-memory cache with
a shared store such as Redis, exporting metrics to Prometheus, and
offloading heavy work to background workers.

