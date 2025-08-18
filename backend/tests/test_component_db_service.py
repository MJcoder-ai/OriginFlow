import asyncio
import os
import sys
from pathlib import Path

# Set up environment variables for testing
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services.component_db_service import ComponentDBService  # noqa: E402


def test_get_by_part_number():
    async def _run():
        svc = ComponentDBService()
        await svc.ingest("panel", "P1", {"name": "Test Panel"})

        comp = await svc.get_by_part_number("P1")
        assert comp is not None
        assert comp.get("name") == "Test Panel"

        missing = await svc.get_by_part_number("missing")
        assert missing is None

    asyncio.run(_run())
