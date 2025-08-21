#!/usr/bin/env python3
"""Check FastAPI routes for missing endpoints."""

from backend.main import app

print("FastAPI Routes:")
print("=" * 50)

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
        print(f"  {route.path} - {methods}")

print("\nCritical Route Check:")
print("=" * 50)

for route in critical_routes:
    if route in mounted_routes:
        print(f"✅ {route}")
    else:
        print(f"❌ MISSING: {route}")

# Check for deprecated routes
deprecated_routes = [
    "/api/v1/ai/plan",
    "/api/v1/ai/analyze-design",
]

print(f"\nDeprecated Route Check:")
print("=" * 50)

for route in deprecated_routes:
    if route in mounted_routes:
        print(f"⚠️  DEPRECATED BUT STILL MOUNTED: {route}")
    else:
        print(f"✅ {route} (not mounted - good)")
