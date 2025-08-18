import pytest
from backend.services.ai.state_action_resolver import StateAwareActionResolver
from backend.schemas.analysis import DesignSnapshot
from backend.schemas.analysis import CanvasComponent


@pytest.mark.asyncio
async def test_resolver_selects_panel_with_text_and_priors(monkeypatch):
    class _DummyEmbedder:
        def encode(self, text: str):
            return 1.0 if "panel" in text.lower() else 0.1

    from backend.services.ai import state_action_resolver as sar  # type: ignore
    monkeypatch.setattr(sar, "get_sentence_embedder", lambda: _DummyEmbedder())

    resolver = StateAwareActionResolver()
    snap = DesignSnapshot(components=[CanvasComponent(id="c1", name="Comp", type="generic_panel", x=0, y=0)], links=[])
    dec = resolver.resolve_add_component("add additional solar panel", snapshot=snap)
    assert dec.action == "add_component"
    assert dec.component_class == "panel"
    assert dec.confidence > 0.2
