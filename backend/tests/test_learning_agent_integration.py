import importlib.util
import sys
import types
from pathlib import Path

import pytest

from backend.services.anonymizer import anonymize
from backend.services.embedding_service import EmbeddingService
from backend.services.reference_confidence_service import ReferenceConfidenceService
from backend.schemas.ai import AiAction, AiActionType


class DummyEmbedder(EmbeddingService):
    async def embed_text(self, texts):  # type: ignore[override]
        return [[0.0, 0.0] for _ in texts]


class InMemoryVectorStore:
    def __init__(self):
        self.data = {}

    async def upsert(self, id, vector, metadata):
        self.data[id] = (vector, metadata)

    async def search(self, query, k, filters=None):
        results = []
        for id, (vec, meta) in self.data.items():
            if filters and any(meta.get(k) != v for k, v in (filters or {}).items()):
                continue
            results.append({"id": id, "score": 1.0, "payload": meta, "vector": vec})
        return results[:k]

    async def delete(self, id):  # pragma: no cover - unused
        self.data.pop(id, None)


@pytest.mark.asyncio
async def test_anonymizer_embedder_vector_store_and_learning_agent(monkeypatch):
    store = InMemoryVectorStore()
    embedder = DummyEmbedder()
    monkeypatch.setattr("backend.services.vector_store.get_vector_store", lambda: store)

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def execute(self, *a, **kw):
            class R:
                def all(self_inner):
                    return []

            return R()

    # Dynamically load learning_agent without triggering side-effects
    agents_pkg = types.ModuleType("backend.agents")
    agents_pkg.__path__ = []
    sys.modules.setdefault("backend.agents", agents_pkg)
    # Provide dummy database session module to avoid real DB/config imports
    session_mod = types.ModuleType("backend.database.session")
    session_mod.SessionMaker = lambda: DummySession()
    sys.modules["backend.database.session"] = session_mod
    la_path = Path(__file__).resolve().parents[1] / "agents" / "learning_agent.py"
    spec = importlib.util.spec_from_file_location("backend.agents.learning_agent", la_path)
    learning_agent = importlib.util.module_from_spec(spec)
    sys.modules["backend.agents.learning_agent"] = learning_agent
    assert spec.loader is not None  # for mypy
    spec.loader.exec_module(learning_agent)

    monkeypatch.setattr(learning_agent, "get_vector_store", lambda: store)
    monkeypatch.setattr(learning_agent, "EmbeddingService", lambda: embedder)
    monkeypatch.setattr(learning_agent, "SessionMaker", lambda: DummySession())

    await store.upsert("1", [0.0, 0.0], {"action_type": "addComponent", "approval": True})
    await store.upsert("2", [0.0, 0.0], {"action_type": "addComponent", "approval": False})

    action = AiAction(action=AiActionType.add_component, payload={"type": "inverter"}, version=1)

    learner = learning_agent.LearningAgent()
    await learner.assign_confidence([action], {"components": []}, [])
    assert 0.4 <= (action.confidence or 0) <= 0.6

    ref = ReferenceConfidenceService(store, embedder, None)
    res = await ref.evaluate_action(action, {}, [])
    assert "confidence" in res and isinstance(res["confidence"], float)

    masked = anonymize("contact me at test@example.com or 555-123-4567")
    assert "[EMAIL]" in masked and "[PHONE]" in masked
