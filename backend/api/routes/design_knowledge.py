from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.services.design_knowledge_service import (
    DesignKnowledgeService,
    DesignVectorCreate,
    DesignVectorSearch,
    get_design_knowledge_service,
)

router = APIRouter(tags=["design-knowledge"])


@router.post("/design/vectors")
async def store_vector(
    payload: DesignVectorCreate,
    svc: DesignKnowledgeService = Depends(get_design_knowledge_service),
) -> dict:
    obj = await svc.store_vector(payload)
    return {"id": obj.id, "meta": obj.meta}


@router.post("/design/vectors/search")
async def search_vectors(
    payload: DesignVectorSearch,
    svc: DesignKnowledgeService = Depends(get_design_knowledge_service),
) -> list[dict]:
    results = await svc.search(payload.vector, payload.limit)
    return [
        {"id": vec.id, "score": score, "meta": vec.meta}
        for vec, score in results
    ]
