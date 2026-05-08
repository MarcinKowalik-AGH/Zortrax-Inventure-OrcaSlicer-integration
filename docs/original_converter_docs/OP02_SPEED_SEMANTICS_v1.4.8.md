# Zortrax Inventure — OP02 speed scaling analysis v2

Scope: native Z-Suite `.zcode` samples from project archives plus current `b1.zcode` / `b3.zcode` pair.

## Key confirmation from b1/b3

`b1`: Print speed +0%, Support Print speed 100%.  `b3`: Print speed -50%, Support Print speed 120%.

Observed scaling:

- model areas: `0x00`, `0x02`, `0x03`, `0x11`, `0x13` scale by global print speed only: e.g. `1200 -> 600`, `3500 -> 1750`, `6400 -> 3200`.
- support-speed-controlled areas: `0x04`, `0x05`, `0x18` scale by global print speed * support print speed: `3500 -> 2100` = `0.5 * 1.2`.
- support surface/interface-like areas: `0x1B`, `0x21` scale by global print speed only: `1800 -> 900`. They must not be treated as ordinary `support_speed`.
- tower `0x1D/0x1E`, travel `0xFC`, purge/retract technical areas are not scaled by the Z-Suite print/support speed sliders.

## Resulting Orca mapping

- `support_speed` should be based mainly on `0x04/0x05/0x18`.
- `support_interface_speed` should be based on `0x1B/0x21`, with the caveat that PETG-based samples show 30 mm/s while many Z-PLA/Z-SUPPORT samples show 35 mm/s. Config uses the project-wide dominant value except where a dedicated 0.30 native sample gave 40 mm/s.
- `wipe_tower_max_purge_speed` remains 33 mm/s (`F2000`).
- acceleration/jerk remain preserved from previous presets because classic `.zcode` exposes OP02 feedrate, not a reliable per-feature acceleration table.

Generated files:

- `b1_b3_OP02_scaling_comparison.csv`
- `op02_area_semantics_and_orca_mapping_v2.csv`
- `v148_process_speed_targets.csv`
- `from_previous_native_analysis_selected.csv`


Converter integration: LOG_ONLY/constants/docs. Motion byte streams remain governed by confirmed converter logic; material mapping already uses PETG-based 0x83.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
