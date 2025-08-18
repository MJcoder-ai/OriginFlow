import pytest

from backend.services.library_selector import LibrarySelector
from backend.schemas.analysis import DesignSnapshot


@pytest.mark.asyncio
async def test_selector_falls_back_when_no_library(monkeypatch):
    sel = LibrarySelector()
    mid, why = await sel.choose_model_or_placeholder("panel", None)
    assert mid is None and "no_real_models_available" in why

