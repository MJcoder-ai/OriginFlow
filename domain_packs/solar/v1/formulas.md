# Solar System Sizing Formulas

This markdown document collects fundamental formulas for sizing and
configuring grid-connected photovoltaic systems.  The formulas are
expressed in plain English and simple mathematical expressions; more
complex derivations and edge cases are deferred to the reasoning
scaffold implemented in the PVDesign template.

## Panel Count

To determine the number of photovoltaic modules (panels) required to
meet a desired **target power**:

```text
panel_count = ceil(target_power / panel_power)
```

Where:
* `target_power` is the total DC power (W) requested by the user.
* `panel_power` is the nominal rated power (W) of a single panel.

## Array Power

Once the panel count is known, the total array power can be computed:

```text
array_power = panel_count * panel_power
```

## Inverter Count

PV arrays require inverters to convert DC to AC.  The number of
inverters can be estimated by dividing the array power by the
``inverter_capacity`` (W), typically with an overhead factor to
account for future expansion and derating:

```text
inverter_count = ceil(array_power / inverter_capacity)
```

## Miscellaneous Relationships

* **Roof area utilisation:** the total area required by `panel_count`
  modules is `panel_count * panel_area`.  This should not exceed the
  available roof area.
* **Budget constraint:** the cost of the PV array is
  `panel_count * panel_price + inverter_count * inverter_price` and
  should not exceed the user's budget if provided.
