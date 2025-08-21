from __future__ import annotations
import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

# Optional OpenTelemetry logging instrumentation; safely ignored if absent/disabled.
try:
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
except Exception:  # pragma: no cover
    LoggingInstrumentor = None  # type: ignore

LOG_JSON = os.getenv("LOG_JSON", "true").lower() in ("1", "true", "yes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
INCLUDE_OTEL = os.getenv("LOG_INCLUDE_OTEL", "true").lower() in ("1", "true", "yes")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "originflow-backend")

# Pull per-request/tenant context (soft dependency; graceful fallback)
def _get_tenant_id() -> Optional[str]:
    try:
        from backend.utils.tenant_context import get_tenant_id
        return get_tenant_id()
    except Exception:
        return None

def _get_request_id() -> Optional[str]:
    try:
        from backend.observability.request_context import get_request_id
        return get_request_id()
    except Exception:
        return None

class _JsonFormatter(logging.Formatter):
    """
    Minimal-alloc JSON formatter with OTEL correlation, tenant & request IDs.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Base envelope
        payload: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int(time.time()*1000)%1000:03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach OTEL correlation if present
        if INCLUDE_OTEL:
            # LoggingInstrumentor sets these on the record, when tracing is active
            trace_id = getattr(record, "otelTraceID", None)
            span_id = getattr(record, "otelSpanID", None)
            sampled = getattr(record, "otelTraceSampled", None)
            if trace_id:
                payload["trace_id"] = str(trace_id)
            if span_id:
                payload["span_id"] = str(span_id)
            if sampled is not None:
                payload["trace_sampled"] = bool(sampled)
            payload["service"] = SERVICE_NAME
        # Tenant & request ids (contextvars)
        tid = _get_tenant_id()
        if tid:
            payload["tenant_id"] = tid
        rid = _get_request_id()
        if rid:
            payload["request_id"] = rid
        # Exception info
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

class _ConsoleFormatter(logging.Formatter):
    """
    Human-friendly single-line formatter (fallback when LOG_JSON=false).
    Includes OTEL ids if available.
    """
    def format(self, record: logging.LogRecord) -> str:
        parts = [f"[{record.levelname}] {record.name}: {record.getMessage()}"]
        tid = _get_tenant_id()
        rid = _get_request_id()
        if INCLUDE_OTEL:
            trace_id = getattr(record, "otelTraceID", None)
            span_id = getattr(record, "otelSpanID", None)
            if trace_id:
                parts.append(f"(trace={trace_id})")
            if span_id:
                parts.append(f"(span={span_id})")
        if tid:
            parts.append(f"(tenant={tid})")
        if rid:
            parts.append(f"(req={rid})")
        if record.exc_info:
            parts.append(self.formatException(record.exc_info))
        return " ".join(parts)

def init_logging() -> None:
    """
    Initialize structured logging across app + uvicorn + access logs.
    Idempotent; safe to call at import time.
    """
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    # Configure root logger with a single stream handler
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(_JsonFormatter() if LOG_JSON else _ConsoleFormatter())
    root.addHandler(handler)

    # Ensure app and uvicorn loggers don't retain their own handlers
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "backend"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel(level)

    # Instrument OTEL logging if available — adds otelTraceID/span to records
    if INCLUDE_OTEL and LoggingInstrumentor:
        try:
            LoggingInstrumentor().instrument(set_logging_format=False)
        except Exception:
            # Non-fatal; logs still work without OTEL enrichment
            pass
