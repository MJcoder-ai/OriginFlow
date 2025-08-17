# Domain Modelling and Calculation Engines

This document describes OriginFlow’s approach to modelling the
requirements of different engineering domains and computing sizing
metrics from user inputs and component libraries.  These concepts
support the AI planner and validation pipeline by ensuring that
every design includes the necessary components and that system sizes
meet user requirements.

## Domain categories

For each supported domain (e.g. solar PV, HVAC, water pumping),
OriginFlow defines a set of component **categories** that are
required, optional or accessory.  Categories map directly to the
``type`` property of components in the ODL graph.

| Domain | Required categories               | Optional categories                | Accessory categories            |
|-------|-----------------------------------|------------------------------------|---------------------------------|
| PV    | `panel`, `inverter`               | `battery`, `charger`, `optimizer`, `monitor` | `mount`, `combiner_box`        |
| HVAC  | `compressor`, `air_handler`       | `condenser`, `evaporator`, `thermostat` | `filter`, `humidifier`         |
| Water | `pump`, `controller`              | `tank`, `sensor`                    | `valve`, `filter`               |

These mappings are defined in `backend/domain/domain_rules.py`.  The
function `missing_required_categories(snapshot, domain)` returns
which required categories are absent from a given design snapshot.

## Calculation engines

Calculation engines compute sizing and performance metrics based on
the user’s requirements and the current design snapshot.  They are
implemented as classes inheriting from `BaseCalculationEngine` in
`backend/services/calculation_engines.py`.  Each engine exposes a
`compute()` method which returns a dictionary of calculated values.

### PVCalculationEngine

This engine estimates the number of solar panels required to meet a
target power.  It assumes a fixed panel rating of 300 W.  When a
requirement includes a `target_power` field (in watts), the engine
computes `panel_count = ceil(target_power / 300)`.  Future versions
should inspect actual panel specifications from the component
library or snapshot to determine panel wattage.

Example:

```python
from backend.services.calculation_engines import PVCalculationEngine
from backend.schemas.analysis import DesignSnapshot

engine = PVCalculationEngine()
requirements = {"target_power": 5000}
snapshot = DesignSnapshot(components=[], links=[], requirements=requirements)
result = await engine.compute(requirements, snapshot)
print(result['panel_count'])  # 17 panels to meet 5 kW
```

### HVACCalculationEngine and WaterCalculationEngine

These engines provide stubs for future implementations.  They will
compute compressor/air handler sizes and pump capacities based on
thermal loads and hydraulic requirements.  Contributions are
welcome to flesh out these engines.

## Integrating domain checks

The AI planner should leverage domain categories to ensure all
required components are present.  When a user command like “design
a 10 kW solar system” is parsed, the planner should:

1. Inspect the session’s snapshot and call
   `missing_required_categories(snapshot, "pv")` to find missing
   categories.
2. Invoke the relevant calculation engine (e.g. `PVCalculationEngine`)
   to compute sizes (e.g. number of panels) from the user’s
   requirements.
3. Propose actions to add missing components and size them
   appropriately.

These checks are complementary to the compatibility engine (which
verifies electrical, mechanical and communication constraints) and
help ensure that designs are complete and meet user goals.

