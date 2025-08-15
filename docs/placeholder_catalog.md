# Placeholder Component Catalog (Phase 21)

To enable full system design without immediately selecting specific
hardware, OriginFlow uses **placeholder components**—generic stand-ins for
real parts.  These placeholders ensure that all necessary nodes and
connections exist in the design graph from the start.  When the user
is ready to choose specific products, the placeholders can be swapped
with real components matching their categories.

## Electrical Protection Devices

| Placeholder          | Default Attributes                            | Replacement Categories                 |
|---------------------|-----------------------------------------------|----------------------------------------|
| `generic_mcb`       | Rating `16A`, 1 pole, curve `B`, phase `AC`  | MCB, Circuit Breaker                  |
| `generic_rccb`      | Residual current `30 mA`, 2 poles, AC phase   | RCCB, Residual Current Device         |
| `generic_spd`       | Max voltage `275 V`, type `II`                | SPD, Surge Protector, Lightning Arrester|
| `generic_ac_isolator` | Rating `20A`, 2 poles, AC phase            | AC Isolator, Disconnect Switch        |
| `generic_dc_combiner` | Strings `2`, voltage `1000 V`                | DC Combiner Box, String Combiner       |
| `generic_distribution_board` | Rating `63A`, modules `4`             | Distribution Board, Panel Board        |
| `generic_battery_fuse` | Rating `125A`, voltage `600 V`            | Fuse, Battery Fuse                     |

## Structural and Mounting Accessories

| Placeholder             | Default Attributes                              | Replacement Categories          |
|------------------------|-------------------------------------------------|---------------------------------|
| `generic_mounting_rail`| Length `2 m`, material `Aluminium`, profile `40×40`| Mounting Rail, DIN Rail, PV Rail|
| `generic_panel_clamp`  | Type `mid` (mid/end), material `Aluminium`        | Panel Clamp, Mid Clamp, End Clamp|
| `generic_mcb_busbar`   | Poles `4`, length `0.5 m`                         | Busbar, MCB Busbar             |

## Auxiliary and Miscellaneous Components

| Placeholder                | Default Attributes                         | Replacement Categories        |
|---------------------------|--------------------------------------------|-------------------------------|
| `generic_optimiser`       | Power `350 W`, voltage `60 V`             | Optimiser, DC Optimiser        |
| `generic_rapid_shutdown`  | Activation `manual`, voltage `600 V`      | Rapid Shutdown, RSD Device      |
| `generic_cable_gland`     | Size `M32`, material `Nylon`             | Cable Gland, Conduit Gland      |

## Usage

The placeholder catalog is defined in `backend/services/placeholder_components.py`.  Each
entry includes default attributes to guide initial sizing and
connections, plus a list of categories used to search for real
components when replacing placeholders.  Agents and planners can
import this module to retrieve the catalog via `get_placeholder_catalog()`.

Future expansions may add more placeholders (e.g. EV chargers,
optimised inverter connectors) or refine default attributes.  When
adding new placeholders, update this document to keep the catalog
current.

## Developer Guidance

For step-by-step instructions on how to add new placeholder component types or create
domain agents that consume them, consult the [developer onboarding guide](developer_guide.md).
The guide explains how to modify the `PLACEHOLDER_COMPONENT_TYPES` catalogue, update this
document and integrate placeholders into agents and planners.
