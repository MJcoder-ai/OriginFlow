"""Vector store abstraction for OriginFlow.

This module defines a simple protocol for interacting with a vector
database and provides implementations for Qdrant and Chroma.  Both
implementations expose the same asynchronous interface for upserting
vectors, searching for nearest neighbours and deleting records.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Protocol


class VectorStore(Protocol):
    """Protocol for vector store operations."""

    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        ...

    async def search(self, query: List[float], k: int, filters: Dict[str, Any] | None) -> List[Dict[str, Any]]:
        ...

    async def delete(self, id: str) -> None:
        ...


def get_vector_store() -> VectorStore:
    """Instantiate a vector store based on environment configuration."""
    backend = os.getenv("VECTOR_BACKEND", "qdrant").lower()
    if backend == "chroma":
        return ChromaVectorStore()
    return QdrantVectorStore()


try:
    from qdrant_client import QdrantClient  # type: ignore
    from qdrant_client.http import models as rest  # type: ignore
except ImportError:
    QdrantClient = None  # type: ignore
    rest = None  # type: ignore


class QdrantVectorStore:
    """Qdrant-based vector store."""

    def __init__(self,
                 host: str | None = None,
                 collection_name: str | None = None,
                 vector_size: int | None = None) -> None:
        if QdrantClient is None:
            raise RuntimeError("qdrant-client package is not installed")
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION", "ai_action_vectors")
        self.vector_size = vector_size or int(os.getenv("VECTOR_SIZE", "384"))
        self.client = QdrantClient(host=self.host, prefer_grpc=True)
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            if rest is None:
                raise RuntimeError("qdrant-client REST models unavailable")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "embedding": rest.VectorParams(size=self.vector_size, distance=rest.Distance.COSINE)
                },
            )

    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        point = rest.PointStruct(
            id=id,
            vector={"embedding": vector},
            payload=metadata,
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])

    async def search(self, query: List[float], k: int, filters: Dict[str, Any] | None) -> List[Dict[str, Any]]:
        filter_obj = None
        if filters:
            conds = [rest.FieldCondition(key=key, match=rest.MatchValue(value=val)) for key, val in filters.items()]
            filter_obj = rest.Filter(must=conds)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=("embedding", query),
            limit=k,
            filter=filter_obj,
        )
        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload or {},
                "vector": r.vector.get("embedding") if r.vector else None,
            }
            for r in results
        ]

    async def delete(self, id: str) -> None:
        self.client.delete(collection_name=self.collection_name, points_selector=rest.PointIdsList(points=[id]))


try:
    import chromadb  # type: ignore
except ImportError:
    chromadb = None  # type: ignore


class ChromaVectorStore:
    """Chroma-based vector store."""

    def __init__(self, collection_name: str | None = None, persist_dir: str | None = None) -> None:
        if chromadb is None:
            raise RuntimeError("chromadb package is not installed")
        self.collection_name = collection_name or os.getenv("CHROMA_COLLECTION", "ai_action_vectors")
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "/data/chroma")
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        self.collection.add(ids=[id], embeddings=[vector], metadatas=[metadata])

    async def search(self, query: List[float], k: int, filters: Dict[str, Any] | None) -> List[Dict[str, Any]]:
        where = filters or {}
        results = self.collection.query(
            query_embeddings=[query],
            n_results=k,
            where=where,
        )
        ids = results.get("ids", [[]])[0]
        dists = results.get("distances", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        embeds = results.get("embeddings", [[]])[0]
        return [
            {
                "id": ids[i],
                "score": dists[i],
                "payload": metas[i] or {},
                "vector": embeds[i] if embeds else None,
            }
            for i in range(len(ids))
        ]

    async def delete(self, id: str) -> None:
        self.collection.delete(ids=[id])
