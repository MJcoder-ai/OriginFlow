import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from datetime import datetime, timezone

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.main import app  # noqa: E402
from backend.services.file_service import FileService  # noqa: E402
from backend.models.file_asset import FileAsset  # noqa: E402

client = TestClient(app)


async def _fake_create(self, data: dict):
    data.setdefault("uploaded_at", datetime.now(timezone.utc))
    data.setdefault("parsed_at", None)
    data.setdefault("parsed_payload", None)
    return FileAsset(**data)


def test_upload_file(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.api.routes.files.generate_id", lambda _: "asset_00000000-0000-0000-0000-000000000000")
    monkeypatch.setattr(FileService, "create_asset", _fake_create)
    file_path = tmp_path / "foo.txt"
    file_path.write_text("hello")

    with file_path.open("rb") as f:
        resp = client.post(
            "/api/v1/files/upload",
            files={"file": ("foo.txt", f, "text/plain")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "foo.txt"
    assert data["mime"] == "text/plain"
    assert data["size"] == 5
    # Verify file was saved in static uploads directory
    saved = Path("backend/static/uploads") / data["id"] / "foo.txt"
    assert saved.exists()


async def _fake_list_assets(self):
    return [
        FileAsset(
            id="a1",
            filename="a.txt",
            mime="text/plain",
            size=1,
            url="/u/a.txt",
            uploaded_at=datetime.now(timezone.utc),
        )
    ]


def test_list_files(monkeypatch):
    monkeypatch.setattr(FileService, "list_assets", _fake_list_assets)
    resp = client.get("/api/v1/files/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list) and data[0]["id"] == "a1"
