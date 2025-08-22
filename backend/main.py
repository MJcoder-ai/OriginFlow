"""FastAPI application startup for OriginFlow."""
from __future__ import annotations

import uvicorn
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.services.anonymizer_service import AnonymizerService
from backend.services.embedding_service import EmbeddingService
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.routes.components_attributes import include_component_attributes_routes
from backend.middleware.security import (
    SecurityMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestValidationMiddleware,
)
from fastapi.middleware.cors import CORSMiddleware

from backend.ops.request_id import RequestIDMiddleware
from backend.ops.health import router as system_router
from backend.ops.metrics import router as ops_metrics_router, track_request
from backend.api.routes.odl_plan import router as planner_router

# ---- Logging (init first so all subsequent imports use structured logs) ----
if not logging.getLogger().handlers:
    try:
        from backend.observability.logging import init_logging
        init_logging()
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy AI services and ensure database tables exist.

    FastAPI does not call startup event handlers when a custom lifespan
    is used, so we must create tables here. This ensures that new ORM
    models (e.g. Memory and TraceEvent) exist before requests hit the DB.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Initializing AI services")
    app.state.anonymizer = AnonymizerService()
    app.state.embedder = EmbeddingService()
    logger.info("AI services initialized successfully")
    # Create any new database tables.  When using a custom lifespan, startup
    # event handlers are not executed, so we must create missing tables here.
    try:
        from backend.database.session import engine as async_engine  # type: ignore
        from backend.models import Base  # type: ignore
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        # Do not crash if table creation fails; log an error
        logger.error(f"Database table creation failed: {exc}", exc_info=True)

    app.state.ai_ready = True

    yield
    logger.info("Cleaning up AI services.")


app = FastAPI(title="OriginFlow API", lifespan=lifespan)

# Ensure a stable flag exists for /readyz without changing behavior.
if not hasattr(app.state, "ai_ready"):
    app.state.ai_ready = False

# ---- Observability (safe no-ops if disabled/missing) ----
try:
    from backend.observability.tracing import init_tracing
    init_tracing(app)
except Exception:
    pass
try:
    from backend.api.routes.metrics import router as metrics_router
    app.include_router(metrics_router)  # /metrics (see RBAC flag)
except Exception:
    pass

# ---- Ensure per-request logging context (request_id) ----
try:
    from backend.middleware.log_context import LogContextMiddleware
    app.add_middleware(LogContextMiddleware)
except Exception:
    pass

# ---- HTTP metrics middleware ----
try:
    from backend.middleware.http_metrics import HTTPMetricsMiddleware
    app.add_middleware(HTTPMetricsMiddleware)
except Exception:
    pass

# ---- Optional test-only routes (enable in tests) ----
import os
if os.getenv("ENABLE_TEST_ROUTES", "0") == "1":
    try:
        from backend.api.routes import test_only as test_only_router
        app.include_router(test_only_router.router, prefix="/__test__")
    except Exception:
        pass

# Add request ID middleware early for correlation
app.add_middleware(RequestIDMiddleware)

# Add security middleware (order matters!)
app.add_middleware(SecurityMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# Relax rate limits for common read-only endpoints in dev
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=300,
    burst_requests=30,
    exempt_paths={
        "/health",
        "/docs",
        "/openapi.json",
        f"{settings.api_prefix}/links/",
        f"{settings.api_prefix}/files/",
        f"{settings.api_prefix}/components/",
    },
)
app.add_middleware(RequestValidationMiddleware)
# --- CORS (dev) --------------------------------------------------------------
# Allow common localhost frontends and permit headers like If-Match used for
# optimistic concurrency when calling /api/v1/ai/act. Configure allowed origins
# via `ORIGINFLOW_CORS_ORIGINS`. Use `*` or empty to allow all origins.
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:8082",
]
_cfg = os.getenv("ORIGINFLOW_CORS_ORIGINS", ",".join(_default_origins)).strip()
_use_regex = _cfg in {"", "*"}
_origins = [o.strip() for o in _cfg.split(",") if o.strip() and o.strip() != "*"]

if _use_regex:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=".*",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "If-Match",
            "X-Request-ID",
            "Accept",
        ],
        expose_headers=["ETag", "X-Request-ID"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "If-Match",
            "X-Request-ID",
            "Accept",
        ],
        expose_headers=["ETag", "X-Request-ID"],
    )

# (RequestIDMiddleware installed above)


@app.middleware("http")
async def _metrics_mw(request: Request, call_next):
    """
    Tiny metrics middleware. Increments a few counters keyed by route prefixes.
    Deliberately minimal; swap with Prometheus later if desired.
    """
    response: Response = await call_next(request)
    try:
        await track_request(request.url.path, request.method, response.status_code)
    except Exception:
        # Do not let metrics ever break a request
        pass
    return response
# Note: table creation moved to `lifespan` above. The startup handler is
# retained only for reference and is never called.

from backend.api.routes import (
    components,
    links,
    ai_act,
    ai_apply,  # Intent Firewall endpoint
    files,
    ai_tools,
    datasheet_parse,
    compatibility,
    feedback_v2,
    design_knowledge,
    naming_policy,
    memory,
    traces,
    me,
    odl,
    requirements,
    snapshots,
    versioning,
    metrics_json,
    layout,
    governance,
    tenant_settings,
    approvals,
)

# Import authentication components
from backend.auth.auth import fastapi_users, auth_backend
from backend.auth.schemas import UserRead, UserCreate, UserUpdate

# Import error handling
from backend.utils.exceptions import (
    OriginFlowException, 
    ErrorHandler,
    AuthenticationError,
    ValidationError
)
from backend.utils.enhanced_logging import setup_logging, get_logger

# Initialize logging
setup_logging(log_level="INFO", json_logs=True)
logger = get_logger(__name__)


app.state.limiter = Limiter(key_func=get_remote_address)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add comprehensive error handling
app.add_exception_handler(OriginFlowException, ErrorHandler.handle_originflow_exception)
app.add_exception_handler(HTTPException, ErrorHandler.handle_http_exception)
app.add_exception_handler(Exception, ErrorHandler.handle_general_exception)

# Log any uncaught exceptions; let FastAPI/Starlette default handling proceed for HTTPException.
@app.exception_handler(Exception)
async def _log_uncaught(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        # Defer to framework's handler (it will still pass through CORS middleware).
        raise exc
    logger = logging.getLogger("backend.main")
    logger.exception("Uncaught exception on %s %s", request.method, request.url)
    # Return a minimal JSON; still passes through CORSMiddleware.
    return JSONResponse(status_code=500, content={
        "error_code": "HTTP_500",
        "message": "Internal server error",
    })

# Resolve the static directory relative to this file and ensure it exists
_static_root = Path(__file__).resolve().parent / "static"
_static_root.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_root)), name="static")

app.include_router(system_router)
app.include_router(ops_metrics_router)
app.include_router(planner_router, prefix=settings.api_prefix)
app.include_router(components.router, prefix=settings.api_prefix)
app.include_router(links.router, prefix=settings.api_prefix)
app.include_router(files.router, prefix=settings.api_prefix)
app.include_router(ai_act.router, prefix=settings.api_prefix)
app.include_router(ai_apply.router, prefix=settings.api_prefix)  # Intent Firewall
app.include_router(ai_tools.router, prefix=settings.api_prefix)
app.include_router(datasheet_parse.router, prefix=settings.api_prefix)
app.include_router(compatibility.router, prefix=settings.api_prefix)

# Design knowledge base endpoints for persisting and querying design embeddings
app.include_router(design_knowledge.router, prefix=settings.api_prefix)

app.include_router(naming_policy.router, prefix=settings.api_prefix)
app.include_router(feedback_v2.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(traces.router, prefix=settings.api_prefix)
app.include_router(me.router, prefix=settings.api_prefix)
app.include_router(odl.router, prefix=settings.api_prefix)
app.include_router(requirements.router, prefix=settings.api_prefix)
app.include_router(snapshots.router, prefix=settings.api_prefix)
app.include_router(versioning.router, prefix=settings.api_prefix)
app.include_router(metrics_json.router, prefix=settings.api_prefix)
app.include_router(layout.router, prefix=settings.api_prefix)
app.include_router(governance.router, prefix=settings.api_prefix)
app.include_router(tenant_settings.router, prefix=settings.api_prefix)
app.include_router(approvals.router, prefix=settings.api_prefix)

# Include authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend), 
    prefix="/auth/jwt", 
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

include_component_attributes_routes(app)


@app.get("/")
async def read_root() -> dict[str, str]:
    """Health check endpoint."""
    return {"message": "Welcome to the OriginFlow API"}


def main() -> None:
    """Entry point for ``originflow-backend`` console script."""
    log_config = Path(__file__).with_name("logging.dev.json")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=str(log_config),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
