#!/usr/bin/env python3
"""Check FastAPI routes for missing endpoints."""

import logging
from backend.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("FastAPI Routes:")
logger.info("=" * 50)

# Check for specific critical routes
critical_routes = [
    "/api/v1/odl/sessions/{session_id}/plan",
    "/api/v1/ai/act",
    "/api/v1/odl/{session_id}/view",
    "/api/v1/odl/sessions",
]

mounted_routes = set()
for route in app.routes:
    if hasattr(route, 'path'):
        mounted_routes.add(route.path)
        methods = getattr(route, 'methods', ['N/A'])
        logger.info("  %s - %s", route.path, methods)

logger.info("\nCritical Route Check:")
logger.info("=" * 50)

for route in critical_routes:
    if route in mounted_routes:
        logger.info("✅ %s", route)
    else:
        logger.error("❌ MISSING: %s", route)

# Check for deprecated routes
deprecated_routes = [
    "/api/v1/ai/plan",
    "/api/v1/ai/analyze-design",
]

logger.info("\nDeprecated Route Check:")
logger.info("=" * 50)

for route in deprecated_routes:
    if route in mounted_routes:
        logger.warning("⚠️  DEPRECATED BUT STILL MOUNTED: %s", route)
    else:
        logger.info("✅ %s (not mounted - good)", route)
