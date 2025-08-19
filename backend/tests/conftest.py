"""Pytest configuration for backend tests.

This module sets default environment variables so that test cases can run
without requiring real credentials or authentication tokens.  Individual tests
can override these values if needed.
"""

import os

# Use a dummy OpenAI API key so components depending on it can initialize.
os.environ.setdefault("OPENAI_API_KEY", "test")

# Use an in-memory SQLite database for faster tests.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Disable authentication for tests that don't supply tokens.
os.environ.setdefault("ENABLE_AUTH", "false")

