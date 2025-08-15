"""Placeholder component definitions and management."""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from backend.schemas.odl import PlaceholderComponent


# Standard placeholder component definitions
PLACEHOLDER_COMPONENT_TYPES: Dict[str, PlaceholderComponent] = {
    "generic_panel": PlaceholderComponent(
        type="generic_panel",
        default_attributes={
            "power": 400,  # Watts
            "voltage": 24,  # Volts
            "efficiency": 0.2,  # 20%
            "area": 2.0,  # Square meters
            "weight": 20.0,  # kg
            "temperature_coefficient": -0.004,  # %/°C
            "max_system_voltage": 1000,  # V
        },
        replacement_categories=["panel", "pv_module", "solar_panel"],
        sizing_rules={
            "min_power": 100,
            "max_power": 800,
            "preferred_power_range": [300, 500],
            "area_per_watt": 0.005,  # m²/W
        },
        validation_rules={
            "required_attributes": ["power", "voltage"],
            "power_tolerance": 0.1,  # ±10%
            "voltage_compatibility": [12, 24, 48],
        }
    ),
    
    "generic_inverter": PlaceholderComponent(
        type="generic_inverter",
        default_attributes={
            "capacity": 5000,  # Watts
            "efficiency": 0.95,  # 95%
            "input_voltage_range": [200, 600],  # V
            "output_voltage": 240,  # V
            "max_input_current": 25,  # A
            "topology": "string",
            "grid_tie": True,
        },
        replacement_categories=["inverter", "string_inverter", "power_optimizer", "microinverter"],
        sizing_rules={
            "min_capacity": 1000,
            "max_capacity": 50000,
            "oversizing_factor": 1.2,  # Allow 20% oversizing
            "undersizing_factor": 0.8,  # Allow 20% undersizing
        },
        validation_rules={
            "required_attributes": ["capacity", "efficiency"],
            "min_efficiency": 0.90,
            "max_dc_ac_ratio": 1.35,
        }
    ),
    
    "generic_mount": PlaceholderComponent(
        type="generic_mount",
        default_attributes={
            "load_rating": 50,  # kg per mount
            "tilt_angle": 30,  # degrees
            "material": "aluminum",
            "wind_rating": 150,  # km/h
            "snow_load": 2400,  # Pa
            "roof_type": "pitched",
            "panels_per_mount": 1,
        },
        replacement_categories=["mounting", "rail", "clamp", "roof_mount"],
        sizing_rules={
            "load_safety_factor": 2.0,
            "wind_safety_factor": 1.5,
            "max_span": 4.0,  # meters
        },
        validation_rules={
            "required_attributes": ["load_rating", "material"],
            "min_load_rating": 20,  # kg
            "approved_materials": ["aluminum", "stainless_steel", "galvanized_steel"],
        }
    ),
    
    "generic_cable": PlaceholderComponent(
        type="generic_cable",
        default_attributes={
            "gauge": "10AWG",
            "voltage_rating": 600,  # V
            "ampacity": 30,  # A
            "length_m": 10.0,  # meters
            "insulation": "XLPE",
            "conductor": "copper",
            "temperature_rating": 90,  # °C
            "uv_resistant": True,
        },
        replacement_categories=["cable", "wire", "dc_cable", "pv_wire"],
        sizing_rules={
            "voltage_drop_limit": 0.03,  # 3%
            "ampacity_safety_factor": 1.25,
            "max_length": 100,  # meters
        },
        validation_rules={
            "required_attributes": ["gauge", "voltage_rating", "ampacity"],
            "min_voltage_rating": 300,  # V
            "approved_conductors": ["copper", "aluminum"],
        }
    ),
    
    "generic_fuse": PlaceholderComponent(
        type="generic_fuse",
        default_attributes={
            "rating_A": 15,  # Amperes
            "voltage_rating": 600,  # V
            "type": "DC",
            "interrupting_capacity": 10000,  # A
            "response_time": "fast",
            "temperature_derating": 0.8,
        },
        replacement_categories=["fuse", "breaker", "disconnect", "combiner"],
        sizing_rules={
            "safety_factor": 1.25,
            "max_continuous_current": 0.8,  # 80% of rating
        },
        validation_rules={
            "required_attributes": ["rating_A", "voltage_rating"],
            "min_interrupting_capacity": 5000,  # A
            "approved_types": ["DC", "AC", "universal"],
        }
    ),
    
    "generic_battery": PlaceholderComponent(
        type="generic_battery",
        default_attributes={
            "capacity_kwh": 10,  # kWh
            "voltage": 48,  # V
            "chemistry": "LiFePO4",
            "cycle_life": 6000,
            "depth_of_discharge": 0.8,  # 80%
            "round_trip_efficiency": 0.95,  # 95%
            "max_charge_rate": 0.5,  # C-rate
            "max_discharge_rate": 1.0,  # C-rate
        },
        replacement_categories=["battery", "energy_storage", "battery_pack"],
        sizing_rules={
            "min_capacity": 1,  # kWh
            "max_capacity": 100,  # kWh
            "voltage_compatibility": [12, 24, 48, 96],
        },
        validation_rules={
            "required_attributes": ["capacity_kwh", "voltage", "chemistry"],
            "min_cycle_life": 3000,
            "approved_chemistries": ["LiFePO4", "Li-ion", "Lead-acid"],
        }
    ),
    
    "generic_monitoring": PlaceholderComponent(
        type="generic_monitoring",
        default_attributes={
            "communication": "WiFi",
            "data_logging": True,
            "alerts": True,
            "web_interface": True,
            "mobile_app": True,
            "api_access": True,
            "power_consumption": 5,  # Watts
        },
        replacement_categories=["monitoring", "gateway", "data_logger"],
        sizing_rules={
            "max_devices": 50,
            "update_frequency": 60,  # seconds
        },
        validation_rules={
            "required_attributes": ["communication"],
            "approved_protocols": ["WiFi", "Ethernet", "Cellular", "Zigbee"],
        }
    ),
    # Electrical protection devices
    "generic_mcb": PlaceholderComponent(
        type="generic_mcb",
        default_attributes={
            "rating": "16A",
            "poles": 1,
            "curve": "B",
            "phase": "AC",
        },
        replacement_categories=["MCB", "Circuit Breaker"],
    ),
    "generic_rccb": PlaceholderComponent(
        type="generic_rccb",
        default_attributes={
            "rating": "30mA",
            "poles": 2,
            "phase": "AC",
        },
        replacement_categories=["RCCB", "Residual Current Device"],
    ),
    "generic_spd": PlaceholderComponent(
        type="generic_spd",
        default_attributes={
            "rating": "275V",
            "type": "II",
        },
        replacement_categories=["SPD", "Surge Protector", "Lightning Arrester"],
    ),
    "generic_ac_isolator": PlaceholderComponent(
        type="generic_ac_isolator",
        default_attributes={
            "rating": "20A",
            "poles": 2,
            "phase": "AC",
        },
        replacement_categories=["AC Isolator", "Disconnect Switch"],
    ),
    "generic_dc_combiner": PlaceholderComponent(
        type="generic_dc_combiner",
        default_attributes={
            "strings": 2,
            "voltage": "1000V",
        },
        replacement_categories=["DC Combiner Box", "String Combiner"],
    ),
    # Structural and mounting accessories
    "generic_mounting_rail": PlaceholderComponent(
        type="generic_mounting_rail",
        default_attributes={
            "length_m": 2.0,
            "material": "Aluminium",
            "profile": "40x40",
        },
        replacement_categories=["Mounting Rail", "DIN Rail", "PV Rail"],
    ),
    "generic_panel_clamp": PlaceholderComponent(
        type="generic_panel_clamp",
        default_attributes={
            "type": "mid",
            "material": "Aluminium",
        },
        replacement_categories=["Panel Clamp", "Mid Clamp", "End Clamp"],
    ),
    "generic_mcb_busbar": PlaceholderComponent(
        type="generic_mcb_busbar",
        default_attributes={
            "poles": 4,
            "length_m": 0.5,
        },
        replacement_categories=["Busbar", "MCB Busbar"],
    ),
    # Auxiliary and miscellaneous components
    "generic_optimiser": PlaceholderComponent(
        type="generic_optimiser",
        default_attributes={
            "power": "350W",
            "voltage": "60V",
        },
        replacement_categories=["Optimiser", "DC Optimiser"],
    ),
    "generic_rapid_shutdown": PlaceholderComponent(
        type="generic_rapid_shutdown",
        default_attributes={
            "activation_method": "manual",
            "voltage": "600V",
        },
        replacement_categories=["Rapid Shutdown", "RSD Device"],
    ),
    "generic_distribution_board": PlaceholderComponent(
        type="generic_distribution_board",
        default_attributes={
            "rating": "63A",
            "modules": 4,
        },
        replacement_categories=["Distribution Board", "Panel Board"],
    ),
    "generic_cable_gland": PlaceholderComponent(
        type="generic_cable_gland",
        default_attributes={
            "size": "M32",
            "material": "Nylon",
        },
        replacement_categories=["Cable Gland", "Conduit Gland"],
    ),
    "generic_battery_fuse": PlaceholderComponent(
        type="generic_battery_fuse",
        default_attributes={
            "rating": "125A",
            "voltage": "600V",
        },
        replacement_categories=["Fuse", "Battery Fuse"],
    ),
}


class PlaceholderComponentService:
    """Service for managing placeholder components."""
    
    def __init__(self):
        self.component_types = PLACEHOLDER_COMPONENT_TYPES
    
    def get_placeholder_type(self, component_type: str) -> Optional[PlaceholderComponent]:
        """Get placeholder component definition by type."""
        return self.component_types.get(component_type)
    
    def get_all_placeholder_types(self) -> Dict[str, PlaceholderComponent]:
        """Get all placeholder component definitions."""
        return self.component_types.copy()
    
    def validate_placeholder_attributes(self, component_type: str, attributes: Dict[str, Any]) -> List[str]:
        """Validate placeholder component attributes against rules."""
        errors = []
        placeholder = self.get_placeholder_type(component_type)
        
        if not placeholder:
            return [f"Unknown placeholder type: {component_type}"]
        
        validation_rules = placeholder.validation_rules or {}
        
        # Check required attributes
        required_attrs = validation_rules.get("required_attributes", [])
        for attr in required_attrs:
            if attr not in attributes:
                errors.append(f"Missing required attribute: {attr}")
        
        # Type-specific validations
        if component_type == "generic_panel":
            power = attributes.get("power", 0)
            if power < validation_rules.get("min_power", 0):
                errors.append(f"Panel power {power}W below minimum")
            
        elif component_type == "generic_inverter":
            efficiency = attributes.get("efficiency", 0)
            min_eff = validation_rules.get("min_efficiency", 0)
            if efficiency < min_eff:
                errors.append(f"Inverter efficiency {efficiency} below minimum {min_eff}")
        
        elif component_type == "generic_battery":
            chemistry = attributes.get("chemistry", "")
            approved = validation_rules.get("approved_chemistries", [])
            if chemistry and chemistry not in approved:
                errors.append(f"Battery chemistry {chemistry} not approved")
        
        return errors
    
    def create_placeholder_node(
        self, 
        node_id: str, 
        component_type: str, 
        custom_attributes: Optional[Dict[str, Any]] = None,
        layer: str = "single_line"
    ) -> Dict[str, Any]:
        """Create a placeholder node with default and custom attributes."""
        placeholder = self.get_placeholder_type(component_type)
        if not placeholder:
            raise ValueError(f"Unknown placeholder type: {component_type}")
        
        # Start with default attributes
        attributes = placeholder.default_attributes.copy()
        
        # Apply custom attributes
        if custom_attributes:
            attributes.update(custom_attributes)
        
        # Validate attributes
        validation_errors = self.validate_placeholder_attributes(component_type, attributes)
        if validation_errors:
            raise ValueError(f"Validation errors: {'; '.join(validation_errors)}")
        
        return {
            "id": node_id,
            "type": component_type,
            "data": {
                **attributes,
                "layer": layer,
            },
            "layer": layer,
            "placeholder": True,
            "candidate_components": [],
            "confidence_score": 0.8,  # Default confidence for placeholder
            "replacement_history": []
        }
    
    def get_replacement_categories(self, component_type: str) -> List[str]:
        """Get valid replacement categories for a placeholder type."""
        placeholder = self.get_placeholder_type(component_type)
        return placeholder.replacement_categories if placeholder else []
    
    def estimate_sizing(
        self, 
        component_type: str, 
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate sizing parameters for placeholder components."""
        placeholder = self.get_placeholder_type(component_type)
        if not placeholder:
            return {}
        
        sizing_rules = placeholder.sizing_rules or {}
        estimates = {}
        
        if component_type == "generic_panel":
            target_power = requirements.get("target_power", 0)
            if target_power > 0:
                panel_power = placeholder.default_attributes["power"]
                estimates["count"] = max(1, int(target_power / panel_power))
                estimates["total_power"] = estimates["count"] * panel_power
                
                roof_area = requirements.get("roof_area", 0)
                if roof_area > 0:
                    panel_area = placeholder.default_attributes.get("area", 2.0)
                    max_panels = int(roof_area / panel_area)
                    estimates["count"] = min(estimates["count"], max_panels)
                    estimates["area_utilization"] = (estimates["count"] * panel_area) / roof_area
        
        elif component_type == "generic_inverter":
            target_power = requirements.get("target_power", 0)
            if target_power > 0:
                inverter_capacity = placeholder.default_attributes["capacity"]
                estimates["count"] = max(1, int(target_power / inverter_capacity))
                estimates["total_capacity"] = estimates["count"] * inverter_capacity
                estimates["sizing_ratio"] = target_power / estimates["total_capacity"]
        
        elif component_type == "generic_battery":
            backup_hours = requirements.get("backup_hours", 0)
            target_power = requirements.get("target_power", 0)
            if backup_hours > 0 and target_power > 0:
                required_capacity = target_power * backup_hours / 1000  # kWh
                battery_capacity = placeholder.default_attributes["capacity_kwh"]
                estimates["count"] = max(1, int(required_capacity / battery_capacity))
                estimates["total_capacity"] = estimates["count"] * battery_capacity
                estimates["backup_duration"] = estimates["total_capacity"] * 1000 / target_power
        
        return estimates
    
    def get_compatibility_matrix(self) -> Dict[str, List[str]]:
        """Get compatibility matrix between placeholder types."""
        return {
            "generic_panel": ["generic_inverter", "generic_mount", "generic_cable"],
            "generic_inverter": ["generic_panel", "generic_battery", "generic_monitoring"],
            "generic_battery": ["generic_inverter", "generic_monitoring"],
            "generic_mount": ["generic_panel"],
            "generic_cable": ["generic_panel", "generic_inverter", "generic_fuse"],
            "generic_fuse": ["generic_cable", "generic_panel"],
            "generic_monitoring": ["generic_inverter", "generic_battery"]
        }


# Global service instance
placeholder_service = PlaceholderComponentService()


def get_placeholder_service() -> PlaceholderComponentService:
    """Get the global placeholder component service instance."""
    return placeholder_service


def get_placeholder_catalog() -> Dict[str, PlaceholderComponent]:
    """Return a copy of the placeholder component catalogue."""
    return placeholder_service.get_all_placeholder_types()
