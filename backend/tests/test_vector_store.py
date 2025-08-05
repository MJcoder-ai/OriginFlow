# backend/tests/test_vector_store.py
"""Tests for vector store initialization."""
import os
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services.vector_store import (
    QdrantVectorStore,
    NoOpVectorStore,
    get_vector_store,
)


def test_get_vector_store_falls_back(monkeypatch):
    """Returns a no-op store when initialization fails."""
    monkeypatch.setenv("VECTOR_BACKEND", "qdrant")

    def boom(self, *_, **__):  # pragma: no cover - executed in test
        raise RuntimeError("boom")

    monkeypatch.setattr(QdrantVectorStore, "__init__", boom)
    store = get_vector_store()
    assert isinstance(store, NoOpVectorStore)
