"""Tests for :mod:`backend.services.metrics_service`."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / "backend" / "services" / "metrics_service.py"
spec = importlib.util.spec_from_file_location("metrics_service", module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
MetricsService = module.MetricsService


def test_metrics_service_records_counts_and_latency() -> None:
    service = MetricsService()
    service.increment_counter("events")
    service.increment_counter("events", 2)
    service.record_latency("op", 0.5)
    service.record_latency("op", 1.0)

    metrics = service.get_metrics()
    assert metrics["events"] == 3.0
    assert metrics["op_avg"] == pytest.approx(0.75, rel=1e-6)

