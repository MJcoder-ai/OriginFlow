"""
Domain registry (Phase 7)

Loads domain configuration from `backend/domains/domain.yaml`. If PyYAML is not
available, falls back to built-in defaults equivalent to the YAML file.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

_BUILTIN = {
    "PV": {
        "tools_enabled": [
            "generate_wiring", "generate_mounts", "add_monitoring",
            "make_placeholders", "replace_placeholders"
        ],
        "placeholder_mappings": {
            "generic_panel": ["panel", "pv_module", "solar_panel"],
            "generic_inverter": ["inverter", "string_inverter"],
            "generic_battery": ["battery", "energy_storage"],
        },
        "risk_overrides": {"replace_placeholders": "medium"},
    },
    "HVAC": {
        "tools_enabled": ["make_placeholders", "replace_placeholders"],
        "placeholder_mappings": {
            "generic_fan": ["fan", "blower"],
            "generic_pump": ["pump", "hvac_pump"],
        },
        "risk_overrides": {"replace_placeholders": "medium"},
    },
    "Water": {
        "tools_enabled": ["make_placeholders", "replace_placeholders"],
        "placeholder_mappings": {
            "generic_pump": ["pump", "water_pump"],
        },
        "risk_overrides": {"replace_placeholders": "medium"},
    },
}


@lru_cache(maxsize=1)
def _load_config() -> Dict:
    path = Path(__file__).with_name("domain.yaml")
    if path.exists():
        try:
            import yaml  # type: ignore
            with path.open("rt", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data
        except Exception:
            # Fall back to built-in config if YAML parsing fails
            return _BUILTIN
    return _BUILTIN


def get_domain_config(name: str) -> Dict:
    cfg = _load_config()
    return cfg.get(name, cfg.get("PV", {}))


def categories_for_placeholder(domain: str, placeholder_type: str) -> List[str]:
    cfg = get_domain_config(domain)
    return list(cfg.get("placeholder_mappings", {}).get(placeholder_type, []))


def tools_enabled(domain: str) -> List[str]:
    cfg = get_domain_config(domain)
    return list(cfg.get("tools_enabled", []))


def risk_override(domain: str, task: str) -> Optional[str]:
    cfg = get_domain_config(domain)
    return (cfg.get("risk_overrides", {}) or {}).get(task)
