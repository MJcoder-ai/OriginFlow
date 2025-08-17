"""Service for generating human-friendly component names.

This module implements logic to construct component names from metadata
extracted during datasheet parsing. It consults the current naming policy
defined in :mod:`backend.config` and applies a template with sensible
fallbacks. The resulting name can be used as the default ``name`` when
creating or updating a ``ComponentMaster`` record.
"""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - import fallback for isolated test environments
    from backend.services.component_naming_policy import get_naming_policy
except Exception:  # pragma: no cover
    import importlib.util
    from pathlib import Path

    MODULE_PATH = Path(__file__).with_name("component_naming_policy.py")
    spec = importlib.util.spec_from_file_location(
        "component_naming_policy", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    get_naming_policy = module.get_naming_policy  # type: ignore


class ComponentNamingService:
    """Generate component names from parsed metadata."""

    @staticmethod
    def generate_name(metadata: Dict[str, Any], template: str | None = None) -> str:
        """
        Construct a human-friendly component name based on the provided metadata.

        The service retrieves the active naming policy (template and version)
        using :func:`backend.services.component_naming_policy.get_naming_policy`.
        Placeholders in the template (e.g. ``{manufacturer}``, ``{part_number}``,
        ``{rating}``, ``{category}``, ``{series_name}``) are populated from
        ``metadata``. If critical fields are missing, the service supplies
        sensible defaults or omits the corresponding parts of the name.

        Args:
            metadata: The dictionary of fields extracted from the datasheet.
                Expected keys include ``manufacturer``, ``part_number``,
                ``category``, ``series_name``, ``power``, ``capacity`` and
                ``voltage``. Alternative keys such as ``mfg`` or ``pn`` are
                also recognised.
            template: Optional custom template to override the policy template.

        Returns:
            The formatted component name. Consecutive whitespace is collapsed
            into a single space, and leading/trailing whitespace is removed.
        """
        policy = get_naming_policy()
        fmt = template or policy.get("template", "{manufacturer} {part_number}")

        manufacturer = (
            metadata.get("manufacturer")
            or metadata.get("mfg")
            or metadata.get("maker")
            or ""
        )
        part_number = (
            metadata.get("part_number")
            or metadata.get("pn")
            or metadata.get("partNumber")
            or ""
        )
        category = metadata.get("category") or metadata.get("device_type") or ""
        series_name = metadata.get("series_name") or ""

        rating: str = ""
        for key in (
            "power",
            "rated_power",
            "max_power",
            "pmax",
            "capacity",
            "capacity_kwh",
            "voltage",
            "nominal_voltage",
        ):
            val = metadata.get(key)
            if val:
                rating = str(val).strip()
                break

        values: Dict[str, str] = {
            "manufacturer": manufacturer.strip(),
            "part_number": part_number.strip(),
            "category": category.strip(),
            "series_name": series_name.strip(),
            "rating": rating.strip(),
        }

        try:
            name = fmt.format(**values)
        except KeyError as exc:
            missing_key = str(exc).strip("'")
            name = fmt.replace(f"{{{missing_key}}}", "")
            name = name.format(**values)

        return " ".join(name.split()).strip()


__all__ = ["ComponentNamingService"]

