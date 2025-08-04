import pytest

from backend.services.anonymizer import anonymize
from backend.services.embedding_service import EmbeddingService
from backend.services.reference_confidence_service import ReferenceConfidenceService
from backend.agents.learning_agent import LearningAgent
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
    monkeypatch.setattr("backend.agents.learning_agent.get_vector_store", lambda: store)
    monkeypatch.setattr("backend.agents.learning_agent.EmbeddingService", lambda: embedder)

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

    monkeypatch.setattr("backend.agents.learning_agent.SessionMaker", lambda: DummySession())

    await store.upsert("1", [0.0, 0.0], {"action_type": "addComponent", "approval": True})
    await store.upsert("2", [0.0, 0.0], {"action_type": "addComponent", "approval": False})

    action = AiAction(action=AiActionType.add_component, payload={"type": "inverter"}, version=1)
    learner = LearningAgent()
    await learner.assign_confidence([action], {"components": []}, [])
    assert 0.4 <= (action.confidence or 0) <= 0.6

    ref = ReferenceConfidenceService(store, embedder, None)
    res = await ref.evaluate_action(action, {}, [])
    assert "confidence" in res and isinstance(res["confidence"], float)

    masked = anonymize("contact me at test@example.com or 555-123-4567")
    assert "[EMAIL]" in masked and "[PHONE]" in masked
