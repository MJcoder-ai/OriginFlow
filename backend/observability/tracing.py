from __future__ import annotations
import os
import logging

TRACING_ENABLED = os.getenv("TRACING_ENABLED", "false").lower() in ("1","true","yes")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "originflow-backend")
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

def init_tracing(app=None):
    """
    Safe initializer. If OpenTelemetry libs are missing or TRACING_ENABLED=false, this is a no-op.
    """
    if not TRACING_ENABLED:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import SERVICE_NAME as _SN, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.starlette import StarletteInstrumentor

        resource = Resource.create({_SN: SERVICE_NAME})
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces"))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        if app is not None:
            # Instrument the FastAPI/Starlette app
            try:
                FastAPIInstrumentor.instrument_app(app)
            except Exception:
                StarletteInstrumentor().instrument()
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).warning("Tracing init failed: %s", e)
