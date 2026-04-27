# OrcaSlicer profiles

The `presets/` directory contains two independent `.orca_printer` bundles.

## Dual

File:

```text
Zortrax Inventure 0.4 nozzle - dual.orca_printer
```

Contents:

- printer: `Zortrax Inventure 0.4 nozzle - dual`,
- nozzle: `0.4`, `0.4`,
- bed area: `135 x 135`,
- height: `130`,
- default process: `0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual`,
- default filaments: `Z-PLA`, `Z-SUPPORT`,
- min layer: `0.08`,
- max layer: `0.3`,
- `single_extruder_multi_material = 0`.

Processes:

| Process | Layer | First layer | Support filament |
|---|---:|---:|---:|
| `0.08mm Ultra Quality ... - dual` | `0.08` | `0.2` | `2` |
| `0.15mm Quality ... - dual` | `0.15` | `0.2` | `2` |
| `0.20mm Standard ... - dual` | `0.2` | `0.2` | `2` |
| `0.30mm Draft ... - dual` | `0.3` | `0.2` | `2` |

## Single

File:

```text
Zortrax Inventure 0.4 nozzle - single.orca_printer
```

Contents:

- printer: `Zortrax Inventure 0.4 nozzle - single`,
- nozzle: `0.4`,
- bed area: `135 x 135`,
- height: `130`,
- default process: `0.15mm Quality @Zortrax Inventure 0.4 nozzle - single`,
- default filament: `Z-PLA`,
- min layer: `0.08`,
- max layer: `0.3`,
- `single_extruder_multi_material = 0`.

Single processes preserve the technological parameters from dual but use:

```text
support_filament = 0
support_interface_filament = 0
```

so T1 is not used as support filament.

## Filaments

Both bundles include native Zortrax materials, external materials, and `BASF Ultrafuse BVOH`.

## Maintenance rule

When renaming a preset, update its visible name, settings id, JSON filename inside the archive, `bundle_structure.json`, and all `compatible_printers` references.
