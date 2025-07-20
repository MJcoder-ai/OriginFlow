import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.main import app  # noqa: E402

client = TestClient(app)

class FakeResp:
    def __init__(self, content: str) -> None:
        self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]

class DummyClient:
    class Chat:
        class Completions:
            async def create(self, *args, **kwargs):
                return FakeResp('{"pn": "123"}')

        completions = Completions()

    chat = Chat()


def test_parse_datasheet(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.api.routes.datasheet_parse.extract_text", lambda f: "dummy text")
    import backend.api.deps as deps
    client_obj = deps.get_ai_client()
    async def fake_create(*args, **kwargs):
        return FakeResp('{"pn": "123"}')
    monkeypatch.setattr(client_obj.chat.completions, "create", fake_create)

    pdf = tmp_path / "a.pdf"
    pdf.write_text("pdf")
    with pdf.open("rb") as f:
        resp = client.post("/api/v1/parse-datasheet", files={"file": ("a.pdf", f, "application/pdf")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["fields"] == {"pn": "123"}

