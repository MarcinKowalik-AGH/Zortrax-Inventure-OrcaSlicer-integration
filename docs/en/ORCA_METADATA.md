# OrcaSlicer metadata mapping

The converter uses three data sources:

1. the `ORCA METADATA` block,
2. standard Orca comments,
3. `ZORTRAX_*` markers in Machine G-code / Change filament G-code.

## `ORCA METADATA` block

The converter looks for a block such as:

```gcode
; ===== ORCA METADATA BEGIN =====
; key=value
; ===== ORCA METADATA END =====
```

Important keys:

| Orca metadata | Converter role |
|---|---|
| `process` | process name for diagnostics/reporting |
| `filament_t0`, `filament_type_t0` | model material T0, mapped to material code and header offset `62` |
| `filament_t1`, `filament_type_t1` | support/T1 material, mapped to material code and header offset `85` |
| `layer_height` | layer height, header `63`; also affects quality `64` |
| `support_threshold_angle` | support angle, header `66` |
| `infill_density` | infill, header `65` |
| `support` | support enabled flag; affects single/dual decision and triplet `58..60` |
| `support_type` | support type for reporting and helper decisions |
| `travel_speed` | travel speed; converter converts mm/s to mm/min |
| `retraction_speed_t0`, `retraction_speed_t1` | retraction speeds |
| `deretraction_speed_t0`, `deretraction_speed_t1` | deretraction/purge speeds |
| `nozzle_temperature_initial_layer_t0`, `nozzle_temperature_initial_layer_t1` | tool temperatures before startup purge |
| `nozzle_temperature_t0`, `nozzle_temperature_t1` | fallback tool temperatures |
| `curr_bed_type` | bed type selection |
| `bed_temp_*_initial`, `bed_temp_*` | bed temperature depending on plate type |

## Fallback comments

If full `ORCA METADATA` is not available, the converter can use comments:

| Comment | Meaning |
|---|---|
| `; estimated printing time = ...` | print time, header `54..57` |
| `; filament used [mm] = model,support` | filament lengths, headers `73..74` and `77..78` |
| `; filament_type = ...` | fallback model/support material |
| `; filament_settings_id = ...` | fallback material from preset name |
| `; layer_height = ...` | fallback layer height |
| `; sparse_infill_density = ...` | fallback infill |
| `; support_threshold_angle = ...` | fallback support angle |
| `; travel_speed = ...` | fallback travel feedrate |
| `; retraction_speed = ...` | fallback retract speed |
| `; deretraction_speed = ...` | fallback deretract speed |

## Single vs dual

A job is treated as single-material if support length is `0`, or support is missing/equal to model and there is no real second-material usage.

Then:

- `support_code = model_code`,
- `support_length_mm = 0`,
- triplet `58..60 = 01 02 01`.

For real dual jobs:

- Z-SUPPORT family uses `58..60 = 01 03 00`,
- BASF BVOH uses `58..60 = 01 02 01`.
