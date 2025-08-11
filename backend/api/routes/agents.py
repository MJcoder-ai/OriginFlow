"""API route exposing available tasks and agents."""
from fastapi import APIRouter

from backend.agents.registry import registry

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/tasks")
async def list_tasks() -> dict:
    """Return the list of registered task IDs."""
    return {"tasks": registry.available_tasks()}
