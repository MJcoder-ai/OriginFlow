# backend/config.py
"""Application configuration settings.

Defines environment-driven settings using Pydantic for the backend application.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# ---- Layout provider configuration ----
# LAYOUT_PROVIDER: "elk" | "dagre" | "builtin"
# - "elk": server will call an HTTP ELK endpoint to compute positions.
# - "dagre": server delegates to client (frontend) for layout; server API returns 501.
# - "builtin": server uses the simple layered fallback from layout_engine.py.
LAYOUT_PROVIDER = os.getenv("LAYOUT_PROVIDER", "builtin").lower()
# For "elk" provider, set an ELK HTTP service URL (e.g., http://localhost:7777/elk/layout)
LAYOUT_HTTP_URL = os.getenv("LAYOUT_HTTP_URL", "").strip()

# ---- Edge routing configuration ----
# EDGE_ROUTER_PROVIDER: "elk" | "builtin" | "client"
# - "elk": server calls an ELK HTTP endpoint and parses edge sections.
# - "builtin": server uses a Manhattan router with obstacle avoidance.
# - "client": frontend routes using elkjs and PATCHes paths; server returns 501.
EDGE_ROUTER_PROVIDER = os.getenv("EDGE_ROUTER_PROVIDER", "builtin").lower()


class Settings(BaseSettings):
    """Central configuration accessed across the backend."""

    api_prefix: str = "/api/v1"
    database_url: str
    cors_origin_regex: str = r"http://(localhost|127\.0\.0\.1):\d+$"
    openai_api_key: str
    openai_model_router: str = "gpt-4o-mini"
    openai_model_agents: str = "gpt-4o-mini"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    temperature: float = 0.0
    max_tokens: int = 512
    commands_per_minute: int = 30

    # ------------------------------------------------------------------
    # Component naming policy
    # ------------------------------------------------------------------
    #
    # OriginFlow generates human-friendly component names automatically
    # from datasheet metadata.  The naming convention is controlled by
    # two configuration fields: ``component_name_template`` and
    # ``component_naming_version``.  The template is a Python format
    # string containing placeholders (e.g. ``{manufacturer}``,
    # ``{part_number}``, ``{rating}``, ``{category}``) which are
    # substituted with values extracted from the datasheet during
    # parsing.  The version allows deployments to track changes in
    # naming conventions over time without altering code.
    #
    # Example::
    #
    #     component_name_template = "{manufacturer} {part_number} - {rating} {category}"
    #     component_naming_version = 1
    component_name_template: str = (
        "{manufacturer} {part_number} - {rating} {category}"
    )
    component_naming_version: int = 1

    # Datasheet extraction flags. These booleans control which parsing
    # strategies are applied by `run_parsing_job()`. They can be toggled
    # via environment variables or via a future API.
    use_rule_based: bool = True
    use_table_extraction: bool = True
    use_ai_extraction: bool = True
    use_ocr_fallback: bool = False
    
    # Authentication settings
    secret_key: str = "your-super-secret-key-change-in-production"
    enable_auth: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
