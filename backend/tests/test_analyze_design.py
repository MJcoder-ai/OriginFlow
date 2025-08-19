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

client = TestClient(app)

async def _dummy_handle(self, command: str, snapshot: dict | None = None):
    return []

@pytest.mark.asyncio
async def test_analyze_endpoint(monkeypatch):
    # Debug: check if auth is disabled
    print(f"ENABLE_AUTH env var: {os.environ.get('ENABLE_AUTH')}")
    print(f"settings.enable_auth: {settings.enable_auth}")
    
    # Since ENABLE_AUTH=false is working, we don't need to override dependencies
    monkeypatch.setattr(RouterAgent, "handle", _dummy_handle)
    body = {"command": "validate", "snapshot": {"components": [], "links": []}}
    resp = client.post("/api/v1/ai/analyze-design", json=body)
    assert resp.status_code == 200
