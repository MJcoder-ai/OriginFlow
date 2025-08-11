"""FastAPI application startup for OriginFlow."""
from __future__ import annotations

import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.services.anonymizer_service import AnonymizerService
from backend.services.embedding_service import EmbeddingService
from backend.services.ai_service import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.routes.components_attributes import include_component_attributes_routes
from backend.middleware.request_id import request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy AI services and ensure database tables exist.

    FastAPI does not call startup event handlers when a custom lifespan
    is used, so we must create tables here. This ensures that new ORM
    models (e.g. Memory and TraceEvent) exist before requests hit the DB.
    """
    print("Initializing AI services…")
    app.state.anonymizer = AnonymizerService()
    app.state.embedder = EmbeddingService()
    print("AI services initialized.")
    # Create any new database tables.  When using a custom lifespan, startup
    # event handlers are not executed, so we must create missing tables here.
    try:
        from backend.database.session import engine as async_engine  # type: ignore
        from backend.models import Base  # type: ignore
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        # Do not crash if table creation fails; log an error
        print(f"Database table creation failed: {exc}")

    yield
    print("Cleaning up AI services.")


app = FastAPI(title="OriginFlow API", lifespan=lifespan)
app.middleware("http")(request_id_middleware)





# Note: table creation moved to `lifespan` above. The startup handler is
# retained only for reference and is never called.

# --- import agents once so they self-register --------------------
import backend.agents.component_agent  # noqa: F401
import backend.agents.link_agent  # noqa: F401
import backend.agents.layout_agent  # noqa: F401
import backend.agents.auditor_agent  # noqa: F401
import backend.agents.bom_agent  # noqa: F401
import backend.agents.inventory_agent  # noqa: F401
import backend.agents.datasheet_fetch_agent  # noqa: F401
import backend.agents.system_design_agent  # noqa: F401
import backend.agents.wiring_agent  # noqa: F401
import backend.agents.performance_agent  # noqa: F401
import backend.agents.design_assembly_agent  # noqa: F401
import backend.agents.financial_agent  # noqa: F401
# ----------------------------------------------------------------

from backend.api.routes import (
    components,
    links,
    ai,
    analyze,
    files,
    ai_tools,
    datasheet_parse,
    feedback,
    feedback_v2,
    design_knowledge,
    component_library,
    memory,
    traces,
    me,
    odl,
    requirements,
    versioning,
)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Resolve the static directory relative to this file and ensure it exists
_static_root = Path(__file__).resolve().parent / "static"
_static_root.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_root)), name="static")

app.include_router(components.router, prefix=settings.api_prefix)
app.include_router(links.router, prefix=settings.api_prefix)
app.include_router(files.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)
app.include_router(analyze.router, prefix=settings.api_prefix)
app.include_router(ai_tools.router, prefix=settings.api_prefix)
app.include_router(datasheet_parse.router, prefix=settings.api_prefix)

# Design knowledge base endpoints for persisting and querying design embeddings
app.include_router(design_knowledge.router, prefix=settings.api_prefix)

# Component library search endpoints
app.include_router(component_library.router, prefix=settings.api_prefix)

# Feedback logging endpoint for user decisions on AI actions
app.include_router(feedback.router, prefix=settings.api_prefix)
# Enriched feedback endpoint with vector logging
app.include_router(feedback_v2.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(traces.router, prefix=settings.api_prefix)
app.include_router(me.router, prefix=settings.api_prefix)
app.include_router(odl.router, prefix=settings.api_prefix)
app.include_router(requirements.router, prefix=settings.api_prefix)
app.include_router(versioning.router, prefix=settings.api_prefix)
include_component_attributes_routes(app)


@app.get("/")
async def read_root() -> dict[str, str]:
    """Health check endpoint."""
    return {"message": "Welcome to the OriginFlow API"}


def main() -> None:
    """Entry point for ``originflow-backend`` console script."""
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover
    main()
