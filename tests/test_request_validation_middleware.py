import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.middleware.security import RequestValidationMiddleware


app = FastAPI()
app.add_middleware(RequestValidationMiddleware)


@app.post("/ping")
async def ping():
    return {"ok": True}


client = TestClient(app)


def test_bodyless_post_is_allowed():
    resp = client.post("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_post_with_invalid_content_type_is_rejected():
    with pytest.raises(HTTPException) as exc_info:
        client.post(
            "/ping",
            content="<hi></hi>",
            headers={"Content-Type": "application/xml"},
        )
    assert exc_info.value.status_code == 415
