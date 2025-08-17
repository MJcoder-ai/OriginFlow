"""Tests for the compatibility validation engine."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.schemas.analysis import CanvasComponent, DesignSnapshot  # noqa: E402


def _load_engine_class():
    module_path = ROOT / "backend" / "services" / "compatibility.py"
    spec = importlib.util.spec_from_file_location("backend.services.compatibility", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.CompatibilityEngine


@pytest.mark.asyncio
async def test_compatibility_engine_returns_empty_report() -> None:
    """Engine should return zero issues for stub rule sets."""

    component = CanvasComponent(id="c1", name="Comp", type="generic", x=0, y=0)
    snapshot = DesignSnapshot(components=[component], links=[])

    CompatibilityEngine = _load_engine_class()
    engine = CompatibilityEngine()
    report = await engine.validate_system_compatibility(snapshot)

    assert report.total_issues() == 0
    assert set(report.results.keys()) == {"electrical", "mechanical", "thermal", "communication"}

