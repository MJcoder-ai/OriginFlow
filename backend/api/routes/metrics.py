"""Expose metrics collected by :mod:`backend.services.metrics_service`."""

from fastapi import APIRouter

from backend.services.metrics_service import metrics


router = APIRouter()


@router.get(
    "/metrics",
    summary="Retrieve current metrics",
    description="Return counters and average latencies recorded by the metrics service.",
)
async def get_metrics() -> dict[str, float]:
    """Return current metrics as a dictionary."""

    return metrics.get_metrics()

