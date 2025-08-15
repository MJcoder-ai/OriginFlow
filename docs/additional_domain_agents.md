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

## CrossLayerValidationAgent

The `CrossLayerValidationAgent` performs cross‑layer checks to ensure
the design graph is logically consistent.  When the planner emits a
`validate_design` task, this agent:

- Retrieves the design graph and counts connections for each node.
- Identifies any non‑root node with zero incoming and outgoing
  connections, flagging it as an issue.
- Ensures that every **battery module** is connected to either an
  inverter or the system root.  If a battery is isolated, the agent
  reports this and recommends connecting it.
- Verifies that each **monitoring device** is attached to a target
  component via a communication link.  Unconnected monitoring devices
  are reported with guidance to connect them.
- Compares the number of battery modules to the number of inverters,
  recommending a one‑to‑one ratio when they differ.  If multiple
  batteries are connected to a single inverter, the agent suggests
  balancing storage across inverters.
- Returns an ADPF envelope with a design card summarising the
  validation results, including a list of isolated or misconnected
  components and recommended corrective actions.

These improved validations help detect incomplete designs and
inconsistent topologies early.  Future enhancements may incorporate
load and code compliance checks, structural load verifications and
required monitoring for critical components.  See the developer
onboarding guide for guidelines on extending validation logic.

## NetworkValidationAgent

The `NetworkValidationAgent` checks that all critical devices are
connected to a network.  When the planner emits a
`validate_network` task, this agent:

- Retrieves the design graph and locates network devices, inverters and
  monitoring modules.  It recognises both domain‑specific types
  (`network`, `monitoring`) and generic placeholder types
  (`generic_network`, `generic_monitoring`) to support designs
  produced by the NetworkAgent and MonitoringAgent.
- Verifies that at least one network device exists; if not, it reports
  this as an issue.
- Builds an adjacency map of communication links and checks for each
  inverter and monitoring device whether it is connected (directly or
  transitively) to a network device.
- Returns an ADPF envelope with a design card summarising
  connectivity issues and recommended actions (e.g. add network
  devices and connect them to all inverters and monitoring devices).

This agent complements the network design by ensuring that monitoring
and control paths are complete.  Future versions may incorporate
throughput analysis, redundancy checks and integration with actual
network hardware catalogues.

## Planner Integration

These tasks are mapped to their respective agents in the registry
(`backend/agents/registry.py`).  Each agent is registered with an
appropriate risk class and can add components and links to the ODL
graph or perform validations.  Battery design is ``medium`` risk,
monitoring design is ``low`` risk and validation is ``low`` risk.
They return ADPF envelopes with `status='complete'` when
successfully executed (or a report in the case of validation).

Starting in Phase 22, the planner can emit additional validation
tasks:

- `validate_design` → triggers the CrossLayerValidationAgent.  This
  agent now performs connectivity checks and ensures that batteries and
  monitoring devices are connected to their targets and that the
  battery–inverter ratio is balanced.
- `validate_network` → triggers the NetworkValidationAgent, which
  verifies that all inverters and monitoring devices are connected to
  network devices and that network connectivity paths exist.

Like other validation tasks, these operations are **low risk** and
report issues without modifying the design.  See the developer guide
for details on adding new tasks to the planner and registering them
with the appropriate risk class and capabilities.
