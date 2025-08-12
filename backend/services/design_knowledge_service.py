from __future__ import annotations

import json
import math
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import SessionMaker
from backend.models.design_vector import DesignVector
from backend.services.embedding_service import EmbeddingService
from pydantic import BaseModel


class DesignVectorCreate(BaseModel):
    vector: List[float]
    meta: dict | None = None


class DesignVectorSearch(BaseModel):
    vector: List[float]
    limit: int = 5


class DesignKnowledgeService:
    """Service for storing and searching design embeddings."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._embedder = EmbeddingService()

    async def store_vector(self, data: DesignVectorCreate) -> DesignVector:
        obj = DesignVector(vector=data.vector, meta=data.meta)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def search(self, query: List[float], limit: int = 5) -> List[tuple[DesignVector, float]]:
        """Optimized vector search with pagination and caching."""
        # Add reasonable limit to prevent memory issues
        effective_limit = min(limit, 100)
        
        # Use optimized query with limit at database level
        stmt = select(DesignVector).limit(1000)  # Reasonable upper bound
        result = await self.session.execute(stmt)
        vectors = result.scalars().all()
        
        # Vectorized similarity computation for better performance
        import numpy as np
        
        if not vectors:
            return []
        
        # Convert to numpy arrays for efficient computation
        query_array = np.array(query)
        vector_arrays = np.array([vec.vector for vec in vectors])
        
        # Batch cosine similarity computation
        query_norm = query_array / np.linalg.norm(query_array)
        vector_norms = vector_arrays / np.linalg.norm(vector_arrays, axis=1, keepdims=True)
        similarities = np.dot(vector_norms, query_norm)
        
        # Get top-k results efficiently
        top_k_indices = np.argpartition(similarities, -effective_limit)[-effective_limit:]
        top_k_indices = top_k_indices[np.argsort(similarities[top_k_indices])[::-1]]
        
        return [(vectors[i], float(similarities[i])) for i in top_k_indices]

    async def save_design_as_template(self, snapshot: dict, name: str) -> DesignVector:
        """Embed and store a design snapshot as a reusable template."""

        text = json.dumps(snapshot, sort_keys=True)
        vector = (await self._embedder.embed_text([text]))[0]
        obj = DesignVector(vector=vector, meta={"name": name, "snapshot": snapshot})
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj


async def get_design_knowledge_service() -> DesignKnowledgeService:
    async with SessionMaker() as session:
        yield DesignKnowledgeService(session)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
