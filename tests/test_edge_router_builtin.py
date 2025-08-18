import pytest
import importlib.util
from pathlib import Path

from backend.schemas.analysis import DesignSnapshot, CanvasComponent, Link

spec = importlib.util.spec_from_file_location(
    "edge_router", Path(__file__).resolve().parents[1] / "backend/services/edge_router.py"
)
edge_router = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(edge_router)
route_edges = edge_router.route_edges


@pytest.mark.asyncio
async def test_builtin_router_returns_paths(monkeypatch):
    monkeypatch.setenv("EDGE_ROUTER_PROVIDER", "builtin")
    c1 = CanvasComponent(
        id="A",
        name="A",
        type="panel",
        x=0,
        y=0,
        layout={"single_line": {"x": 100, "y": 100}},
        locked_in_layers={"single_line": True},
    )
    c2 = CanvasComponent(
        id="B",
        name="B",
        type="inverter",
        x=0,
        y=0,
        layout={"single_line": {"x": 400, "y": 100}},
        locked_in_layers={"single_line": True},
    )
    l = Link(id="L1", source_id="A", target_id="B")
    snap = DesignSnapshot(components=[c1, c2], links=[l])
    routes = await route_edges(snap, layer="single_line")
    assert "L1" in routes
    assert len(routes["L1"]) >= 2

