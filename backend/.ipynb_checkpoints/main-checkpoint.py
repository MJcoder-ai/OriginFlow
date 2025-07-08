# backend/main.py
"""FastAPI application for OriginFlow.

Exposes the API router and optional CLI entry point for development.
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from .api import endpoints

app = FastAPI(title="OriginFlow API")
app.include_router(endpoints.router, prefix="/api/v1", tags=["components"])

@app.get("/")
def read_root() -> dict[str, str]:
    """Health check endpoint."""

    return {"message": "Welcome to the OriginFlow API"}


def main() -> None:
    """Entry point for ``originflow-backend`` console script."""

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
