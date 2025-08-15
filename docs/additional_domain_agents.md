# Additional Domain Agents

In future releases, the site planning agent may incorporate
geo-location data, shading analysis and automatic PV layout
optimisation.

## Placeholder Component Catalog

Design agents rely on a **placeholder component catalog** to model
parts of the system before specific hardware choices are made. Phase 21
introduced a set of new electrical, structural and miscellaneous
placeholder types such as miniature circuit breakers (MCB), residual
current devices (RCCB), surge protection devices (SPD), mounting
rails, panel clamps, and optimisers. Each placeholder comes with
default attributes (e.g. current rating, physical dimensions) and a
list of replacement categories to map the generic component to real
products. See `docs/placeholder_catalog.md` for the full list.
