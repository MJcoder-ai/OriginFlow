import os
import sys
import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect

# ensure settings load with dummy env vars
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# prevent proxy variables from interfering with httpx in tests
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(var, None)

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.main import app  # noqa: E402
from backend.database.session import engine  # noqa: E402


async def _table_names() -> list[str]:
    async with engine.begin() as conn:
        return await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())


def test_tables_exist_after_startup():
    """Memory and trace tables should be created during lifespan startup."""
    # Entering the client context triggers lifespan startup.
    with TestClient(app):
        pass
    tables = asyncio.run(_table_names())
    assert "memory" in tables
    assert "trace_event" in tables
