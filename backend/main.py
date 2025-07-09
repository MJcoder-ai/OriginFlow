# backend/main.py
"""FastAPI application startup for OriginFlow."""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes import components, links, ai

app = FastAPI(title="OriginFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(components.router, prefix=settings.api_prefix)
app.include_router(links.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)


@app.get("/")
async def read_root() -> dict[str, str]:
    """Health check endpoint."""

    return {"message": "Welcome to the OriginFlow API"}


def main() -> None:
    """Entry point for ``originflow-backend`` console script."""

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover
    main()
