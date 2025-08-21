# Domains (Phase 7)

Domains are **declarative**. Each domain defines:
- `tools_enabled` — which tools are allowed
- `placeholder_mappings` — how generic placeholders map to real categories
- `risk_overrides` — per-task risk overrides (`low`, `medium`, `high`)

Configuration file: `backend/domains/domain.yaml`.  
Loader: `backend/domains/registry.py`.

## Example
```yaml
PV:
  tools_enabled:
    - generate_wiring
    - generate_mounts
    - add_monitoring
    - make_placeholders
    - replace_placeholders
  placeholder_mappings:
    generic_panel: [panel, pv_module, solar_panel]
    generic_inverter: [inverter, string_inverter]
  risk_overrides:
    replace_placeholders: medium
```

The orchestrator reads the session domain from `ODL.meta.domain`
(`PV` by default) and uses these mappings to build candidate searches and risk
decisions.
