import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set environment variables BEFORE importing any modules
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("ENABLE_AUTH", "false")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.main import app  # noqa: E402
from backend.agents.router_agent import RouterAgent  # noqa: E402
from backend.config import settings  # noqa: E402
from backend.auth.models import User  # noqa: E402
import uuid  # noqa: E402

client = TestClient(app)

async def _dummy_handle(self, command: str, snapshot: dict | None = None):
    return []

def _mock_user():
    """Create a mock user for testing."""
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="",
        is_active=True,
        is_verified=True,
        is_superuser=True,
        tenant_id="default"
    )

@pytest.mark.asyncio
async def test_analyze_endpoint(monkeypatch):
    # Debug: check if auth is disabled
    print(f"ENABLE_AUTH env var: {os.environ.get('ENABLE_AUTH')}")
    print(f"settings.enable_auth: {settings.enable_auth}")
    
    # Override the authentication dependency with FastAPI dependency_overrides
    from backend.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    
    try:
        monkeypatch.setattr(RouterAgent, "handle", _dummy_handle)
        body = {"command": "validate", "snapshot": {"components": [], "links": []}}
        resp = client.post("/api/v1/ai/analyze-design", json=body)
        assert resp.status_code == 200
    finally:
        # Clean up the override
        app.dependency_overrides.clear()
