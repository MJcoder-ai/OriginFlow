# backend/utils/logging.py
"""Structured logging utilities.

Provides a JSON logger configured for stdout using structlog.
"""
from __future__ import annotations

import logging

import structlog


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Return a structured logger bound to ``name``."""

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return structlog.get_logger(name)
