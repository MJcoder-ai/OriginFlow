import pytest
import os
import sys
from pathlib import Path

# Set up environment variables for testing
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.agents.learning_agent import LearningAgent  # noqa: E402
from backend.agents import learning_agent as learning_agent_module  # noqa: E402
from backend.schemas.ai import AiAction, AiActionType  # noqa: E402
from backend.services.anonymizer_service import AnonymizerService  # noqa: E402
from backend.services.embedding_service import EmbeddingService  # noqa: E402
from backend.services.reference_confidence_service import ReferenceConfidenceService  # noqa: E402


class DummyEmbedder(EmbeddingService):
    def __init__(self):
        pass

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
            if filters and any(meta.get(key) != val for key, val in (filters or {}).items()):
                continue
            results.append({"id": id, "score": 1.0, "payload": meta, "vector": vec})
        return results[:k]

    async def delete(self, id):  # pragma: no cover - unused
        self.data.pop(id, None)


@pytest.mark.asyncio
async def test_anonymizer_embedder_vector_store_and_learning_agent(monkeypatch):
    store = InMemoryVectorStore()
    embedder = DummyEmbedder()

    await store.upsert("1", [0.0, 0.0], {"action_type": "addComponent", "approval": True})
    await store.upsert("2", [0.0, 0.0], {"action_type": "addComponent", "approval": False})

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

    monkeypatch.setattr(learning_agent_module, "SessionMaker", lambda: DummySession())
    
    class DummyRefService:
        def __init__(self, *_a, **_kw):
            pass

        async def evaluate_action(self, action, ctx, history):  # type: ignore[override]
            return {"confidence": 0.5, "reasoning": "mock"}

    monkeypatch.setattr(learning_agent_module, "ReferenceConfidenceService", DummyRefService)

    learner = LearningAgent(vector_store=store, embedding_service=embedder)
    action = AiAction(action=AiActionType.add_component, payload={"type": "inverter"}, version=1)
    await learner.assign_confidence([action], {"components": []}, [])
    assert 0.4 <= (action.confidence or 0) <= 0.6

    ref = ReferenceConfidenceService(store, embedder, None)
    res = await ref.evaluate_action(action, {}, [])
    assert "confidence" in res and isinstance(res["confidence"], float)

    anonymizer = AnonymizerService()
    masked = anonymizer.anonymize("contact me at test@example.com or 555-123-4567")
    assert "[EMAIL]" in masked and "[PHONE]" in masked
