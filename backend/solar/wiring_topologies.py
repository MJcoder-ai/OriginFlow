"""
Production-grade wiring topology system for solar installations.
Handles different system architectures and protection device requirements.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import logging
import math

from .component_library import ComponentLibrary, ComponentCategory, ComponentDefinition

logger = logging.getLogger(__name__)

class SystemTopology(Enum):
    """Different solar system wiring topologies"""
    STRING_INVERTER = "string_inverter"
    POWER_OPTIMIZER = "power_optimizer"
    MICROINVERTER = "microinverter"
    BATTERY_STORAGE = "battery_storage"
    COMMERCIAL_THREE_PHASE = "commercial_three_phase"

class ProtectionLevel(Enum):
    """Levels of electrical protection"""
    BASIC = "basic"          # Minimal NEC compliance
    STANDARD = "standard"    # Typical residential
    ENHANCED = "enhanced"    # Commercial/high-reliability
    CRITICAL = "critical"    # Mission-critical systems

@dataclass
class StringConfiguration:
    """Configuration for a PV string"""
    modules_per_string: int
    strings_per_combiner: int
    max_string_voltage: float
    max_string_current: float
    protection_devices: List[str]

@dataclass
class SystemDesignParameters:
    """Parameters for system design"""
    total_power_kw: float
    voltage_system: str  # "208V_3P", "480V_3P", "240V_1P"
    topology: SystemTopology
    protection_level: ProtectionLevel
    
    # Environmental factors
    temperature_ambient_max: float = 40.0  # Celsius
    temperature_module_max: float = 70.0   # Celsius
    
    # Code compliance requirements
    nec_version: str = "2020"
    local_amendments: List[str] = None
    
    # System preferences
    string_sizing_strategy: str = "voltage_optimized"  # or "current_optimized"
    combiner_preference: bool = True  # Use combiner boxes
    monitoring_level: str = "system"  # "system", "string", "module"

class WiringTopologyEngine:
    """Engine for generating production-grade wiring topologies"""
    
    def __init__(self, component_library: ComponentLibrary):
        self.component_library = component_library
        self.nec_rules = self._load_nec_rules()
    
    def design_system_topology(self, parameters: SystemDesignParameters, 
                             available_components: List[str]) -> Dict[str, Any]:
        """Design complete system topology with protection devices"""
        
        logger.info(f"Designing {parameters.topology.value} topology for {parameters.total_power_kw}kW system")
        
        # Select primary components
        modules = self._select_modules(parameters, available_components)
        inverters = self._select_inverters(parameters, available_components)
        
        if not modules or not inverters:
            raise ValueError("Could not find suitable modules or inverters")
        
        # Calculate string configuration
        string_config = self._calculate_string_configuration(modules[0], inverters[0], parameters)
        
        # Design topology based on system type
        if parameters.topology == SystemTopology.STRING_INVERTER:
            return self._design_string_inverter_system(modules[0], inverters[0], string_config, parameters)
        elif parameters.topology == SystemTopology.COMMERCIAL_THREE_PHASE:
            return self._design_commercial_system(modules[0], inverters[0], string_config, parameters)
        else:
            raise ValueError(f"Topology {parameters.topology.value} not implemented")
    
    def _select_modules(self, parameters: SystemDesignParameters, 
                       available_components: List[str]) -> List[ComponentDefinition]:
        """Select appropriate PV modules"""
        modules = self.component_library.get_components_by_category(ComponentCategory.PV_MODULE)
        
        # Filter by availability
        if available_components:
            modules = [m for m in modules if m.id in available_components]
        
        # Sort by power rating (prefer higher wattage for fewer modules)
        modules.sort(key=lambda m: m.electrical_specs.power_max or 0, reverse=True)
        
        return modules[:3]  # Return top 3 options
    
    def _select_inverters(self, parameters: SystemDesignParameters,
                         available_components: List[str]) -> List[ComponentDefinition]:
        """Select appropriate inverters"""
        if parameters.topology == SystemTopology.STRING_INVERTER:
            inverters = self.component_library.get_components_by_category(ComponentCategory.STRING_INVERTER)
        else:
            return []
        
        # Filter by availability and power range
        suitable_inverters = []
        for inv in inverters:
            if available_components and inv.id not in available_components:
                continue
            
            # Check if inverter can handle the system power
            inv_power = inv.electrical_specs.power_max or 0
            if inv_power >= parameters.total_power_kw * 800:  # Allow some undersizing
                suitable_inverters.append(inv)
        
        # Sort by power rating
        suitable_inverters.sort(key=lambda i: i.electrical_specs.power_max or 0)
        
        return suitable_inverters[:3]
    
    def _calculate_string_configuration(self, module: ComponentDefinition, 
                                      inverter: ComponentDefinition,
                                      parameters: SystemDesignParameters) -> StringConfiguration:
        """Calculate optimal string configuration"""
        
        # Get module specifications
        vmp_module = module.electrical_specs.voltage_dc_nominal or 40
        voc_module = module.electrical_specs.voltage_dc_max or 48
        imp_module = module.electrical_specs.current_max or 10
        power_module = module.electrical_specs.power_max or 400
        
        # Get inverter specifications  
        vmax_inverter = inverter.electrical_specs.voltage_dc_max or 1000
        imax_inverter = inverter.electrical_specs.current_max or 25
        
        # Temperature derating factors
        temp_coeff = module.electrical_specs.temperature_coefficient or -0.35
        temp_rise = parameters.temperature_module_max - 25  # STC temperature
        
        # Calculate temperature-corrected voltages
        voc_corrected = voc_module * (1 + temp_coeff/100 * (-40 - 25))  # Cold temperature
        vmp_corrected = vmp_module * (1 + temp_coeff/100 * temp_rise)    # Hot temperature
        
        # Calculate maximum modules per string (voltage limit)
        max_modules_voltage = int(vmax_inverter * 0.95 / voc_corrected)  # 95% safety factor
        
        # Calculate maximum modules per string (current limit)
        max_modules_current = int(imax_inverter / imp_module)
        
        # Use the more restrictive limit
        modules_per_string = min(max_modules_voltage, max_modules_current, 20)  # NEC 690.7 limit
        
        # Ensure minimum string size for inverter operation
        min_modules = int((inverter.electrical_specs.voltage_dc_nominal or 300) / vmp_corrected)
        modules_per_string = max(modules_per_string, min_modules, 8)  # Practical minimum
        
        # Calculate number of strings needed
        total_modules = int(parameters.total_power_kw * 1000 / power_module)
        strings_needed = math.ceil(total_modules / modules_per_string)
        
        # Combiner sizing
        strings_per_combiner = min(strings_needed, 6)  # Standard combiner size
        
        # Determine protection devices needed
        protection_devices = self._determine_protection_devices(parameters, modules_per_string, strings_needed)
        
        return StringConfiguration(
            modules_per_string=modules_per_string,
            strings_per_combiner=strings_per_combiner,
            max_string_voltage=modules_per_string * voc_corrected,
            max_string_current=imp_module,
            protection_devices=protection_devices
        )
    
    def _determine_protection_devices(self, parameters: SystemDesignParameters,
                                    modules_per_string: int, strings_needed: int) -> List[str]:
        """Determine required protection devices based on system and code requirements"""
        
        protection_devices = []
        
        # Always required by NEC
        protection_devices.extend([
            "dc_disconnect_60a",      # NEC 690.13 - DC disconnect
            "ac_breaker_40a_3p",      # NEC 690.64 - AC disconnect  
            "production_meter"         # NEC 690.71 - Monitoring
        ])
        
        # String fusing (NEC 690.9)
        if strings_needed > 2:  # Required when 3+ strings in parallel
            protection_devices.append("string_fuses")
        
        # Combiner box for multiple strings
        if strings_needed > 1 and parameters.topology == SystemTopology.STRING_INVERTER:
            protection_devices.append("dc_combiner_6string")
        
        # Enhanced protection for commercial systems
        if parameters.protection_level in [ProtectionLevel.ENHANCED, ProtectionLevel.CRITICAL]:
            protection_devices.extend([
                "surge_protector_dc",    # DC surge protection
                "surge_protector_ac",    # AC surge protection
                "arc_fault_detector",    # Arc fault detection
                "ground_fault_detector", # Ground fault detection
            ])
        
        # Rapid shutdown (NEC 690.12)
        if parameters.nec_version >= "2017":
            protection_devices.append("rapid_shutdown")
        
        return protection_devices
    
    def _design_string_inverter_system(self, module: ComponentDefinition,
                                     inverter: ComponentDefinition,
                                     string_config: StringConfiguration,
                                     parameters: SystemDesignParameters) -> Dict[str, Any]:
        """Design string inverter system topology"""
        
        total_modules = int(parameters.total_power_kw * 1000 / (module.electrical_specs.power_max or 400))
        num_strings = math.ceil(total_modules / string_config.modules_per_string)
        num_combiners = math.ceil(num_strings / string_config.strings_per_combiner)
        
        # Calculate actual system power
        actual_modules = num_strings * string_config.modules_per_string
        actual_power_kw = actual_modules * (module.electrical_specs.power_max or 400) / 1000
        
        system_design = {
            "topology": SystemTopology.STRING_INVERTER.value,
            "summary": {
                "total_power_kw": actual_power_kw,
                "total_modules": actual_modules,
                "num_strings": num_strings,
                "num_combiners": num_combiners,
                "modules_per_string": string_config.modules_per_string
            },
            "components": {
                "modules": {
                    "component_id": module.id,
                    "quantity": actual_modules,
                    "arrangement": "strings"
                },
                "inverters": {
                    "component_id": inverter.id,
                    "quantity": 1,
                    "sizing_ratio": actual_power_kw / ((inverter.electrical_specs.power_max or 10000) / 1000)
                }
            },
            "protection_devices": {},
            "wiring_instructions": [],
            "code_compliance": {
                "nec_articles": ["690.4", "690.7", "690.8", "690.9", "690.12", "690.13"],
                "calculations": self._generate_nec_calculations(module, inverter, string_config, parameters)
            }
        }
        
        # Add protection devices with quantities
        for device_id in string_config.protection_devices:
            if device_id == "dc_combiner_6string":
                system_design["components"]["combiners"] = {
                    "component_id": device_id,
                    "quantity": num_combiners
                }
            elif device_id == "string_fuses":
                system_design["protection_devices"]["string_fuses"] = {
                    "rating_amps": int(string_config.max_string_current * 1.56),  # NEC 690.8(B)
                    "quantity": num_strings
                }
            else:
                device = self.component_library.get_component(device_id)
                if device:
                    system_design["protection_devices"][device_id] = {
                        "component_id": device_id,
                        "quantity": 1
                    }
        
        # Generate wiring instructions
        system_design["wiring_instructions"] = self._generate_wiring_instructions(
            system_design, string_config, parameters
        )
        
        return system_design
    
    def _design_commercial_system(self, module: ComponentDefinition,
                                inverter: ComponentDefinition,
                                string_config: StringConfiguration,
                                parameters: SystemDesignParameters) -> Dict[str, Any]:
        """Design commercial three-phase system with enhanced protection"""
        
        # Start with string inverter design
        system_design = self._design_string_inverter_system(module, inverter, string_config, parameters)
        
        # Add commercial-specific enhancements
        system_design["topology"] = SystemTopology.COMMERCIAL_THREE_PHASE.value
        
        # Add monitoring at string level
        system_design["monitoring"] = {
            "string_monitoring": True,
            "data_acquisition": "ethernet",
            "remote_monitoring": True
        }
        
        # Enhanced protection for commercial
        system_design["protection_devices"]["arc_fault_circuit_interrupter"] = {
            "component_id": "afci_commercial",
            "quantity": 1
        }
        
        system_design["protection_devices"]["ground_fault_protection"] = {
            "component_id": "gfp_commercial", 
            "quantity": 1
        }
        
        # Three-phase metering
        system_design["components"]["production_meter"] = {
            "component_id": "production_meter_3phase",
            "quantity": 1,
            "monitoring_points": ["L1", "L2", "L3", "N"]
        }
        
        return system_design
    
    def _generate_nec_calculations(self, module: ComponentDefinition,
                                 inverter: ComponentDefinition, 
                                 string_config: StringConfiguration,
                                 parameters: SystemDesignParameters) -> Dict[str, Any]:
        """Generate NEC compliance calculations"""
        
        calculations = {}
        
        # NEC 690.7 - Maximum voltage calculations
        voc_module = module.electrical_specs.voltage_dc_max or 48
        temp_factor = 1.25  # Conservative temperature correction factor
        
        calculations["max_system_voltage"] = {
            "value": string_config.modules_per_string * voc_module * temp_factor,
            "limit": inverter.electrical_specs.voltage_dc_max,
            "compliant": (string_config.modules_per_string * voc_module * temp_factor) <= (inverter.electrical_specs.voltage_dc_max or 1000),
            "nec_reference": "690.7(A)"
        }
        
        # NEC 690.8 - Circuit current calculations  
        isc_module = module.electrical_specs.current_short_circuit or (module.electrical_specs.current_max or 10) * 1.25
        
        calculations["max_circuit_current"] = {
            "value": isc_module * 1.25,  # 125% of Isc
            "nec_reference": "690.8(A)"
        }
        
        # NEC 690.9 - Overcurrent protection
        calculations["overcurrent_protection"] = {
            "string_fuse_rating": isc_module * 1.56,  # 156% rule
            "dc_breaker_rating": string_config.max_string_current * len([x for x in string_config.protection_devices if "combiner" in x]),
            "nec_reference": "690.9(B)"
        }
        
        return calculations
    
    def _generate_wiring_instructions(self, system_design: Dict[str, Any],
                                    string_config: StringConfiguration,
                                    parameters: SystemDesignParameters) -> List[Dict[str, Any]]:
        """Generate detailed wiring instructions"""
        
        instructions = []
        
        # String wiring instructions
        instructions.append({
            "step": 1,
            "description": "Wire PV modules in series to form strings",
            "details": {
                "modules_per_string": string_config.modules_per_string,
                "wire_type": "PV Wire",
                "wire_size": "12 AWG", 
                "connection_type": "MC4 connectors",
                "polarity": "Positive to negative in series"
            },
            "safety_notes": ["Verify polarity", "Use proper torque specifications", "Install during low irradiance"]
        })
        
        # Combiner box connections
        if "combiners" in system_design["components"]:
            instructions.append({
                "step": 2,
                "description": "Connect strings to DC combiner box",
                "details": {
                    "strings_per_combiner": string_config.strings_per_combiner,
                    "fuse_rating": f"{int(string_config.max_string_current * 1.56)}A",
                    "wire_size": "10 AWG",
                    "torque_spec": "35 in-lbs"
                },
                "safety_notes": ["Install string fuses", "Verify ground continuity", "Label all circuits"]
            })
        
        # DC disconnect installation
        instructions.append({
            "step": 3,
            "description": "Install DC disconnect switch",
            "details": {
                "location": "Accessible location per NEC 690.13",
                "rating": "60A/1000V DC",
                "wire_size": "8 AWG",
                "marking": "SOLAR DC DISCONNECT"
            },
            "safety_notes": ["Mount within sight of inverter", "Use appropriate enclosure rating"]
        })
        
        # Inverter connections
        instructions.append({
            "step": 4,
            "description": "Connect DC input to inverter",
            "details": {
                "positive_terminal": "DC+",
                "negative_terminal": "DC-",
                "torque_spec": "40 in-lbs",
                "wire_type": "THWN-2 or PV Wire"
            },
            "safety_notes": ["Verify voltage before connection", "Follow manufacturer torque specs"]
        })
        
        # AC side connections
        instructions.append({
            "step": 5,
            "description": "Connect AC output to electrical panel",
            "details": {
                "breaker_size": "40A 3-pole",
                "wire_size": "8 AWG THWN",
                "connection": "Line side of main breaker or separate disconnect"
            },
            "safety_notes": ["Turn off main breaker", "Verify proper grounding", "Install production meter"]
        })
        
        return instructions
    
    def _load_nec_rules(self) -> Dict[str, Any]:
        """Load NEC code rules and requirements"""
        return {
            "690.4": {
                "title": "Installation Requirements", 
                "key_points": ["Equipment installation", "Working space", "Access"]
            },
            "690.7": {
                "title": "Maximum Voltage",
                "key_points": ["Temperature correction", "Series connection limits"]
            },
            "690.8": {
                "title": "Circuit Current",
                "key_points": ["125% continuous current", "Short circuit current"]
            },
            "690.9": {
                "title": "Overcurrent Protection",
                "key_points": ["Fuse sizing", "156% rule", "Series fusing requirements"]
            },
            "690.12": {
                "title": "Rapid Shutdown",
                "key_points": ["10 feet rule", "Shutdown device requirements"]
            },
            "690.13": {
                "title": "DC Disconnect",
                "key_points": ["Readily accessible", "Marked", "Within sight"]
            }
        }

# Factory function to create topology engine
def create_topology_engine() -> WiringTopologyEngine:
    """Create a wiring topology engine with standard component library"""
    from .component_library import component_library
    return WiringTopologyEngine(component_library)