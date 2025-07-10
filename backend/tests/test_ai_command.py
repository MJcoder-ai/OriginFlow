import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ensure settings load with dummy env vars
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.main import app  # noqa: E402
from backend.agents.router_agent import RouterAgent  # noqa: E402

client = TestClient(app)

async def _dummy_handle(self, command: str):
    return []

@pytest.mark.asyncio
async def test_ai_command_body(monkeypatch):
    monkeypatch.setattr(RouterAgent, "handle", _dummy_handle)
    resp = client.post("/api/v1/ai/command", json={"command": "ping"})
    assert resp.status_code == 200
