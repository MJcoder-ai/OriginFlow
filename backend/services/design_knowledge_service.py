from __future__ import annotations

import math
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import SessionMaker
from backend.models.design_vector import DesignVector
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

    async def store_vector(self, data: DesignVectorCreate) -> DesignVector:
        obj = DesignVector(vector=data.vector, meta=data.meta)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def search(self, query: List[float], limit: int = 5) -> List[tuple[DesignVector, float]]:
        stmt = select(DesignVector)
        result = await self.session.execute(stmt)
        vectors = result.scalars().all()
        scores: List[tuple[DesignVector, float]] = []
        for vec in vectors:
            score = cosine_similarity(query, vec.vector)
            scores.append((vec, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]


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
