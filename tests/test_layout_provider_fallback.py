import pytest
from backend.services.layout_provider import suggest_positions
from backend.schemas.analysis import DesignSnapshot, CanvasComponent


@pytest.mark.asyncio
async def test_builtin_provider_suggests_unlocked_positions(monkeypatch):
    # Force builtin provider for this test
    monkeypatch.setenv("LAYOUT_PROVIDER", "builtin")
    c1 = CanvasComponent(
        id="A",
        name="A",
        type="panel",
        x=0,
        y=0,
        locked_in_layers={"single_line": True},
        layout={"single_line": {"x": 100.0, "y": 100.0}},
    )
    c2 = CanvasComponent(id="B", name="B", type="inverter", x=0, y=0)
    snap = DesignSnapshot(components=[c1, c2], links=[])
    pos = await suggest_positions(snap, layer="single_line")
    assert "B" in pos and "A" not in pos
