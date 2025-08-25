"""
Enhanced placeholder component service that centralizes component definitions
in an external JSON resource. This simplifies maintenance and allows non‑
engineers to update placeholder definitions without modifying code.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from backend.schemas.odl import PlaceholderComponent


def _load_definitions(definitions_path: Optional[str] = None) -> Dict[str, PlaceholderComponent]:
    """
    Load placeholder definitions from a JSON file and merge port definitions.

    The definitions file maps each component type to a specification with keys:
    - default_attributes (dict)
    - replacement_categories (list)
    - sizing_rules (dict, optional)
    - validation_rules (dict, optional)
    A secondary ports file maps types to a list of port templates. If present,
    the ports are attached to the resulting PlaceholderComponent.

    If loading fails, an empty dictionary is returned.
    """
    definitions: Dict[str, PlaceholderComponent] = {}
    if definitions_path is None:
        definitions_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "resources",
            "placeholder_definitions.json",
        )
    # Load raw definitions
    try:
        with open(os.path.abspath(definitions_path), "r", encoding="utf-8") as f:
            raw_defs: Dict[str, Any] = json.load(f)
    except Exception:
        raw_defs = {}
    # Load optional port definitions
    ports_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "resources",
        "placeholder_ports.json",
    )
    try:
        with open(os.path.abspath(ports_path), "r", encoding="utf-8") as pf:
            raw_ports: Dict[str, List[Dict[str, Any]]] = json.load(pf)
    except Exception:
        raw_ports = {}
    # Construct PlaceholderComponent instances
    for comp_type, spec in raw_defs.items():
        definitions[comp_type] = PlaceholderComponent(
            type=comp_type,
            default_attributes=spec.get("default_attributes", {}),
            replacement_categories=spec.get("replacement_categories", []),
            sizing_rules=spec.get("sizing_rules"),
            validation_rules=spec.get("validation_rules"),
            ports=raw_ports.get(comp_type),
        )
    return definitions


class CentralizedPlaceholderService:
    """
    Service responsible for managing placeholder components.

    Unlike the original implementation, this service reads component definitions
    from a JSON file at instantiation. This promotes configuration‑driven
    behaviour and allows administrators to update placeholder definitions
    without touching Python code.
    """

    def __init__(self, component_definitions: Optional[Dict[str, PlaceholderComponent]] = None):
        self.component_types: Dict[str, PlaceholderComponent] = (
            component_definitions or _load_definitions()
        )

    def get_placeholder_type(self, component_type: str) -> Optional[PlaceholderComponent]:
        """Return the PlaceholderComponent definition for the given type."""
        return self.component_types.get(component_type)

    def get_all_placeholder_types(self) -> Dict[str, PlaceholderComponent]:
        """Return a copy of all placeholder component definitions."""
        return self.component_types.copy()

    def validate_placeholder_attributes(
        self, component_type: str, attributes: Dict[str, Any]
    ) -> List[str]:
        """
        Validate attributes for a placeholder component type.
        Returns a list of validation errors (empty if valid).
        """
        errors: List[str] = []
        placeholder = self.get_placeholder_type(component_type)
        
        if not placeholder:
            errors.append(f"Unknown placeholder type: {component_type}")
            return errors
        
        validation_rules = placeholder.validation_rules or {}
        
        # Check required attributes
        required_attrs = validation_rules.get("required_attributes", [])
        for attr in required_attrs:
            if attr not in attributes:
                errors.append(f"Missing required attribute: {attr}")
        
        # Type-specific validation
        if component_type == "generic_panel":
            power = attributes.get("power", 0)
            min_power = validation_rules.get("min_power", 0)
            max_power = validation_rules.get("max_power", float('inf'))
            if power < min_power or power > max_power:
                errors.append(f"Power {power}W outside valid range [{min_power}-{max_power}W]")
        
        elif component_type == "generic_inverter":
            efficiency = attributes.get("efficiency", 0)
            min_efficiency = validation_rules.get("min_efficiency", 0)
            if efficiency < min_efficiency:
                errors.append(f"Efficiency {efficiency} below minimum {min_efficiency}")
        
        elif component_type == "generic_battery":
            chemistry = attributes.get("chemistry", "")
            supported_chemistries = validation_rules.get("supported_chemistries", [])
            if chemistry and supported_chemistries and chemistry not in supported_chemistries:
                errors.append(f"Unsupported battery chemistry: {chemistry}")
        
        return errors

    def create_placeholder_node(
        self,
        node_id: str,
        component_type: str,
        custom_attributes: Optional[Dict[str, Any]] = None,
        layer: str = "single-line",
    ) -> Dict[str, Any]:
        """
        Construct a dictionary representing a placeholder node in the ODL graph.

        Merges the component's default attributes with any custom attributes,
        performs validation, and appends placeholder metadata with ports.
        """
        placeholder = self.get_placeholder_type(component_type)
        if not placeholder:
            raise ValueError(f"Unknown placeholder type: {component_type}")

        attributes = placeholder.default_attributes.copy()
        if custom_attributes:
            attributes.update(custom_attributes)

        validation_errors = self.validate_placeholder_attributes(component_type, attributes)
        if validation_errors:
            raise ValueError(f"Validation errors: {'; '.join(validation_errors)}")

        # Build ports dict keyed by port ID if this component defines ports
        ports: Optional[Dict[str, Dict[str, Any]]] = None
        if placeholder.ports:
            ports = {p["id"]: {k: v for k, v in p.items() if k != "id"} for p in placeholder.ports}

        return {
            "id": node_id,
            "type": component_type,
            "data": {
                **attributes,
                "layer": layer,
            },
            "layer": layer,
            "ports": ports,
            "placeholder": True,
            "candidate_components": [],
            "confidence_score": 0.8,
            "replacement_history": [],
        }

    def estimate_sizing(
        self, component_type: str, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provide sizing estimates for a placeholder type based on provided requirements.
        """
        placeholder = self.get_placeholder_type(component_type)
        if not placeholder:
            return {}

        sizing_rules = placeholder.sizing_rules or {}
        estimates: Dict[str, Any] = {}

        if component_type == "generic_panel":
            target_power = requirements.get("target_power", 0.0)
            if target_power > 0:
                panel_power = placeholder.default_attributes.get("power", 0.0)
                if panel_power > 0:
                    estimates["count"] = max(1, int(target_power / panel_power))
                    estimates["total_power"] = estimates["count"] * panel_power
                    roof_area = requirements.get("roof_area", 0.0)
                    if roof_area > 0:
                        panel_area = placeholder.default_attributes.get("area", 2.0)
                        max_panels = int(roof_area / panel_area)
                        estimates["count"] = min(estimates["count"], max_panels)
                        estimates["area_utilization"] = (
                            estimates["count"] * panel_area
                        ) / roof_area

        elif component_type == "generic_inverter":
            target_power = requirements.get("target_power", 0.0)
            if target_power > 0:
                capacity = placeholder.default_attributes.get("capacity", 0.0)
                if capacity > 0:
                    estimates["count"] = max(1, int(target_power / capacity))
                    estimates["total_capacity"] = estimates["count"] * capacity
                    estimates["sizing_ratio"] = target_power / estimates["total_capacity"]

        elif component_type == "generic_battery":
            backup_hours = requirements.get("backup_hours", 0.0)
            target_power = requirements.get("target_power", 0.0)
            if backup_hours > 0 and target_power > 0:
                required_capacity = target_power * backup_hours / 1000.0  # Convert to kWh
                battery_capacity = placeholder.default_attributes.get("capacity", 0.0)
                if battery_capacity > 0:
                    estimates["count"] = max(1, int(required_capacity / battery_capacity))
                    estimates["total_capacity"] = estimates["count"] * battery_capacity
                    estimates["backup_hours"] = estimates["total_capacity"] * 1000 / target_power

        return estimates

    def get_compatibility_matrix(self) -> Dict[str, List[str]]:
        """
        Return a compatibility matrix showing which component types work together.
        This is a simplified hard-coded matrix for demonstration.
        """
        return {
            "generic_panel": ["generic_inverter", "generic_mount", "generic_cable", "generic_fuse"],
            "generic_inverter": ["generic_panel", "generic_battery", "generic_monitoring", "generic_mcb"],
            "generic_battery": ["generic_inverter", "generic_monitoring", "generic_mcb"],
            "generic_mount": ["generic_panel", "generic_structural"],
            "generic_cable": ["generic_panel", "generic_inverter", "generic_battery"],
            "generic_fuse": ["generic_panel", "generic_dc_combiner"],
            "generic_monitoring": ["generic_inverter", "generic_battery"],
            "generic_mcb": ["generic_inverter", "generic_battery", "generic_ac_isolator"],
            "generic_rccb": ["generic_inverter", "generic_ac_isolator"],
            "generic_surge_protector": ["generic_inverter", "generic_mcb"],
            "generic_ac_isolator": ["generic_inverter", "generic_mcb", "generic_rccb"],
            "generic_dc_combiner": ["generic_panel", "generic_fuse"],
            "generic_structural": ["generic_mount", "generic_panel"]
        }

    def create_placeholder_examples(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate an example node for each defined placeholder type.

        The returned dictionary maps component type to a representative ODL node
        containing default attributes, placeholder metadata, and port definitions.
        """
        examples: Dict[str, Dict[str, Any]] = {}
        for comp_type in self.component_types:
            try:
                examples[comp_type] = self.create_placeholder_node(
                    node_id=f"example_{comp_type}",
                    component_type=comp_type,
                    custom_attributes=None,
                    layer="single-line",
                )
            except Exception:
                continue
        return examples


# Global service instance and convenience functions
_service_instance: Optional[CentralizedPlaceholderService] = None


def get_placeholder_service() -> CentralizedPlaceholderService:
    """Get the global placeholder service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CentralizedPlaceholderService()
    return _service_instance


def get_placeholder_examples() -> Dict[str, Dict[str, Any]]:
    """Convenience function to get placeholder examples."""
    service = get_placeholder_service()
    return service.create_placeholder_examples()


def reload_placeholder_definitions(definitions_path: Optional[str] = None) -> None:
    """Reload placeholder definitions from JSON file."""
    global _service_instance
    new_definitions = _load_definitions(definitions_path)
    _service_instance = CentralizedPlaceholderService(new_definitions)