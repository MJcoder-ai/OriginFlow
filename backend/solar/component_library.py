"""
Production-grade solar component library with comprehensive device support.
Handles protection devices, different wiring topologies, and electrical specifications.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
import json

class ComponentCategory(Enum):
    # Generation
    PV_MODULE = "pv_module"
    
    # Power Electronics
    STRING_INVERTER = "string_inverter"
    POWER_OPTIMIZER = "power_optimizer"
    MICROINVERTER = "microinverter"
    
    # Protection Devices
    DC_COMBINER = "dc_combiner"
    AC_COMBINER = "ac_combiner"
    DISCONNECT_SWITCH = "disconnect_switch"
    CIRCUIT_BREAKER = "circuit_breaker"
    FUSE = "fuse"
    SURGE_PROTECTOR = "surge_protector"
    
    # Monitoring & Control
    PRODUCTION_METER = "production_meter"
    CONSUMPTION_METER = "consumption_meter"
    RAPID_SHUTDOWN = "rapid_shutdown"
    
    # Infrastructure
    CONDUIT = "conduit"
    JUNCTION_BOX = "junction_box"
    GROUNDING = "grounding"
    
    # Energy Storage
    BATTERY = "battery"
    BATTERY_INVERTER = "battery_inverter"


@dataclass
class ElectricalSpecs:
    """Electrical specifications for components"""
    # Voltage specifications
    voltage_dc_max: Optional[float] = None
    voltage_dc_nominal: Optional[float] = None
    voltage_ac_nominal: Optional[float] = None
    
    # Current specifications
    current_max: Optional[float] = None
    current_short_circuit: Optional[float] = None
    
    # Power specifications
    power_max: Optional[float] = None
    power_nominal: Optional[float] = None
    
    # Environmental ratings
    temperature_coefficient: Optional[float] = None
    temperature_range: Optional[tuple] = None
    
    # Protection ratings
    ip_rating: Optional[str] = None
    surge_rating: Optional[str] = None


@dataclass
class ConnectionPort:
    """Represents a connection point on a component"""
    id: str
    type: str  # 'dc_in', 'dc_out', 'ac_in', 'ac_out', 'data', 'ground'
    voltage_type: str  # 'dc', 'ac', 'data'
    max_current: Optional[float] = None
    max_voltage: Optional[float] = None
    is_array: bool = False  # True for combiner inputs that accept multiple connections


@dataclass
class ComponentDefinition:
    """Complete definition of a solar system component"""
    id: str
    name: str
    category: ComponentCategory
    manufacturer: str
    model_number: str
    
    # Electrical specifications
    electrical_specs: ElectricalSpecs
    
    # Connection ports
    ports: List[ConnectionPort]
    
    # Physical properties
    dimensions: Optional[Dict[str, float]] = None  # width, height, depth in mm
    weight: Optional[float] = None  # kg
    
    # Installation requirements
    mounting_type: Optional[str] = None  # roof, ground, wall, pole
    spacing_requirements: Optional[Dict[str, float]] = None
    
    # Code compliance
    certifications: List[str] = field(default_factory=list)  # UL, IEC, etc.
    nec_article: Optional[str] = None
    
    # Cost and availability
    cost_estimate: Optional[float] = None
    lead_time_days: Optional[int] = None


class ComponentLibrary:
    """Production component library with real-world solar components"""
    
    def __init__(self):
        self.components: Dict[str, ComponentDefinition] = {}
        self._initialize_standard_components()
    
    def _initialize_standard_components(self):
        """Initialize with standard solar components"""
        
        # Standard PV Module
        self.add_component(ComponentDefinition(
            id="pv_module_400w",
            name="400W Monocrystalline Solar Panel",
            category=ComponentCategory.PV_MODULE,
            manufacturer="Generic",
            model_number="PV400M",
            electrical_specs=ElectricalSpecs(
                voltage_dc_max=48.7,
                voltage_dc_nominal=41.2,
                current_max=10.8,
                current_short_circuit=11.5,
                power_max=400,
                power_nominal=400,
                temperature_coefficient=-0.35,
                temperature_range=(-40, 85)
            ),
            ports=[
                ConnectionPort("dc_out_pos", "dc_out", "dc", max_current=15, max_voltage=60),
                ConnectionPort("dc_out_neg", "dc_out", "dc", max_current=15, max_voltage=60),
                ConnectionPort("ground", "ground", "ground")
            ],
            dimensions={"width": 2008, "height": 1002, "depth": 35},
            weight=22.5,
            certifications=["UL1703", "IEC61215", "IEC61730"],
            nec_article="690"
        ))
        
        # String Inverter
        self.add_component(ComponentDefinition(
            id="string_inverter_10kw",
            name="10kW String Inverter",
            category=ComponentCategory.STRING_INVERTER,
            manufacturer="Generic",
            model_number="SI10K",
            electrical_specs=ElectricalSpecs(
                voltage_dc_max=1000,
                voltage_dc_nominal=580,
                voltage_ac_nominal=480,
                current_max=25,
                power_max=10000,
                power_nominal=10000,
                temperature_range=(-25, 60)
            ),
            ports=[
                ConnectionPort("dc_in_pos", "dc_in", "dc", max_current=30, max_voltage=1000, is_array=True),
                ConnectionPort("dc_in_neg", "dc_in", "dc", max_current=30, max_voltage=1000, is_array=True),
                ConnectionPort("ac_out_l1", "ac_out", "ac", max_current=15, max_voltage=277),
                ConnectionPort("ac_out_l2", "ac_out", "ac", max_current=15, max_voltage=277),
                ConnectionPort("ac_out_l3", "ac_out", "ac", max_current=15, max_voltage=277),
                ConnectionPort("ac_out_n", "ac_out", "ac", max_current=15, max_voltage=277),
                ConnectionPort("ground", "ground", "ground"),
                ConnectionPort("data", "data", "data")
            ],
            certifications=["UL1741", "IEEE1547"],
            nec_article="690"
        ))
        
        # DC Combiner Box
        self.add_component(ComponentDefinition(
            id="dc_combiner_6string",
            name="6-String DC Combiner Box",
            category=ComponentCategory.DC_COMBINER,
            manufacturer="Generic", 
            model_number="DCB6S",
            electrical_specs=ElectricalSpecs(
                voltage_dc_max=1000,
                current_max=60,
                ip_rating="IP65"
            ),
            ports=[
                ConnectionPort("dc_in_1_pos", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_1_neg", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_2_pos", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_2_neg", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_3_pos", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_3_neg", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_4_pos", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_4_neg", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_5_pos", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_5_neg", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_6_pos", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_in_6_neg", "dc_in", "dc", max_current=15, max_voltage=1000),
                ConnectionPort("dc_out_pos", "dc_out", "dc", max_current=100, max_voltage=1000),
                ConnectionPort("dc_out_neg", "dc_out", "dc", max_current=100, max_voltage=1000),
                ConnectionPort("ground", "ground", "ground")
            ],
            certifications=["UL1741"],
            nec_article="690.64"
        ))
        
        # DC Disconnect Switch
        self.add_component(ComponentDefinition(
            id="dc_disconnect_60a",
            name="60A DC Disconnect Switch",
            category=ComponentCategory.DISCONNECT_SWITCH,
            manufacturer="Generic",
            model_number="DCS60A",
            electrical_specs=ElectricalSpecs(
                voltage_dc_max=1000,
                current_max=60,
                ip_rating="IP65"
            ),
            ports=[
                ConnectionPort("line_pos", "dc_in", "dc", max_current=60, max_voltage=1000),
                ConnectionPort("line_neg", "dc_in", "dc", max_current=60, max_voltage=1000),
                ConnectionPort("load_pos", "dc_out", "dc", max_current=60, max_voltage=1000),
                ConnectionPort("load_neg", "dc_out", "dc", max_current=60, max_voltage=1000),
                ConnectionPort("ground", "ground", "ground")
            ],
            certifications=["UL508"],
            nec_article="690.13"
        ))
        
        # AC Circuit Breaker
        self.add_component(ComponentDefinition(
            id="ac_breaker_40a_3p",
            name="40A 3-Pole AC Circuit Breaker",
            category=ComponentCategory.CIRCUIT_BREAKER,
            manufacturer="Generic",
            model_number="ACB40A3P",
            electrical_specs=ElectricalSpecs(
                voltage_ac_nominal=480,
                current_max=40
            ),
            ports=[
                ConnectionPort("line_l1", "ac_in", "ac", max_current=40, max_voltage=277),
                ConnectionPort("line_l2", "ac_in", "ac", max_current=40, max_voltage=277),
                ConnectionPort("line_l3", "ac_in", "ac", max_current=40, max_voltage=277),
                ConnectionPort("load_l1", "ac_out", "ac", max_current=40, max_voltage=277),
                ConnectionPort("load_l2", "ac_out", "ac", max_current=40, max_voltage=277),
                ConnectionPort("load_l3", "ac_out", "ac", max_current=40, max_voltage=277),
                ConnectionPort("ground", "ground", "ground")
            ],
            certifications=["UL489"],
            nec_article="690.64"
        ))
        
        # Production Meter
        self.add_component(ComponentDefinition(
            id="production_meter",
            name="Solar Production Meter",
            category=ComponentCategory.PRODUCTION_METER,
            manufacturer="Generic",
            model_number="SPM1",
            electrical_specs=ElectricalSpecs(
                voltage_ac_nominal=480,
                current_max=200
            ),
            ports=[
                ConnectionPort("ac_in_l1", "ac_in", "ac", max_current=200, max_voltage=277),
                ConnectionPort("ac_in_l2", "ac_in", "ac", max_current=200, max_voltage=277),
                ConnectionPort("ac_in_l3", "ac_in", "ac", max_current=200, max_voltage=277),
                ConnectionPort("ac_in_n", "ac_in", "ac", max_current=200, max_voltage=277),
                ConnectionPort("ac_out_l1", "ac_out", "ac", max_current=200, max_voltage=277),
                ConnectionPort("ac_out_l2", "ac_out", "ac", max_current=200, max_voltage=277),
                ConnectionPort("ac_out_l3", "ac_out", "ac", max_current=200, max_voltage=277),
                ConnectionPort("ac_out_n", "ac_out", "ac", max_current=200, max_voltage=277),
                ConnectionPort("data", "data", "data"),
                ConnectionPort("ground", "ground", "ground")
            ],
            certifications=["UL2735"],
            nec_article="690.71"
        ))
    
    def add_component(self, component: ComponentDefinition):
        """Add a component to the library"""
        self.components[component.id] = component
    
    def get_component(self, component_id: str) -> Optional[ComponentDefinition]:
        """Get component by ID"""
        return self.components.get(component_id)
    
    def get_components_by_category(self, category: ComponentCategory) -> List[ComponentDefinition]:
        """Get all components of a specific category"""
        return [comp for comp in self.components.values() if comp.category == category]
    
    def find_compatible_components(self, source_component: ComponentDefinition, 
                                 connection_type: str) -> List[ComponentDefinition]:
        """Find components that can connect to the given source component"""
        compatible = []
        
        for component in self.components.values():
            if component.id == source_component.id:
                continue
                
            # Check if target component has compatible input ports
            for port in component.ports:
                if (connection_type == "dc" and 
                    port.type == "dc_in" and 
                    self._check_electrical_compatibility(source_component, component)):
                    compatible.append(component)
                    break
                elif (connection_type == "ac" and 
                      port.type == "ac_in" and 
                      self._check_electrical_compatibility(source_component, component)):
                    compatible.append(component)
                    break
        
        return compatible
    
    def _check_electrical_compatibility(self, source: ComponentDefinition, 
                                      target: ComponentDefinition) -> bool:
        """Check if two components are electrically compatible"""
        # Basic voltage compatibility check
        if (source.electrical_specs.voltage_dc_max and 
            target.electrical_specs.voltage_dc_max):
            if source.electrical_specs.voltage_dc_max > target.electrical_specs.voltage_dc_max:
                return False
        
        # Basic current compatibility check
        if (source.electrical_specs.current_max and 
            target.electrical_specs.current_max):
            if source.electrical_specs.current_max > target.electrical_specs.current_max:
                return False
        
        return True
    
    def export_library(self, file_path: str):
        """Export component library to JSON file"""
        export_data = {}
        for comp_id, component in self.components.items():
            export_data[comp_id] = {
                "name": component.name,
                "category": component.category.value,
                "manufacturer": component.manufacturer,
                "model_number": component.model_number,
                "electrical_specs": component.electrical_specs.__dict__,
                "ports": [port.__dict__ for port in component.ports],
                "certifications": component.certifications,
                "nec_article": component.nec_article
            }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)


# Global component library instance
component_library = ComponentLibrary()