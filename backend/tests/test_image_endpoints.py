import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from fastapi import FastAPI

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

import openai


class DummyAsyncOpenAI:
    def __init__(self, *args, **kwargs):
        pass


openai.AsyncOpenAI = DummyAsyncOpenAI  # type: ignore


sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.api.routes.files import router as files_router  # noqa: E402
from backend.api import deps as deps_module  # noqa: E402
from backend.services.file_service import FileService  # noqa: E402
from backend.models.file_asset import FileAsset  # noqa: E402

app = FastAPI()
app.include_router(files_router, prefix="/api/v1")

async def _override_get_session():
    yield None

app.dependency_overrides[deps_module.get_session] = _override_get_session
app.dependency_overrides[deps_module.get_ai_client] = lambda: None

client = TestClient(app)


async def _fake_list_images(self, asset_id: str):
    return [
        {
            "id": "img1",
            "filename": "a.png",
            "url": "/u/a.png",
            "is_primary": True,
            "is_extracted": True,
            "width": 100,
            "height": 100,
        }
    ]


def test_list_images(monkeypatch):
    monkeypatch.setattr(FileService, "list_images", _fake_list_images)
    resp = client.get("/api/v1/files/asset123/images")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list) and data[0]["id"] == "img1"


async def _fake_upload_images(self, asset_id: str, files):
    return [
        FileAsset(
            id="img1",
            filename="a.png",
            mime="image/png",
            size=10,
            url="/u/a.png",
            uploaded_at=datetime.now(timezone.utc),
            parent_asset_id=asset_id,
            component_id=None,
            is_extracted=False,
            is_primary=False,
            width=100,
            height=100,
        )
    ]


def test_upload_images(monkeypatch, tmp_path):
    monkeypatch.setattr(FileService, "upload_images", _fake_upload_images)
    file_path = tmp_path / "a.png"
    file_path.write_bytes(b"img")
    with file_path.open("rb") as f:
        resp = client.post(
            "/api/v1/files/asset123/images",
            files={"files": ("a.png", f, "image/png")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["filename"] == "a.png"


async def _fake_delete_image(self, asset_id: str, image_id: str):
    return None


def test_delete_image(monkeypatch):
    monkeypatch.setattr(FileService, "delete_image", _fake_delete_image)
    resp = client.delete("/api/v1/files/asset123/images/img1")
    assert resp.status_code == 204


async def _fake_set_primary(self, asset_id: str, image_id: str):
    return None


def test_set_primary_image(monkeypatch):
    monkeypatch.setattr(FileService, "set_primary_image", _fake_set_primary)
    resp = client.patch("/api/v1/files/asset123/images/img1/primary")
    assert resp.status_code == 204
