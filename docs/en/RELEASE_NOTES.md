# Release notes — v1.4.16

## Status

This GitHub update was rebuilt from the real production package:

```text
Zortrax_Inventure_Orca_PRODUCTION_v1.4.16_converter_configs_2026-05-06.zip
```

It includes the converter, base converter file, Windows/macOS launchers, current Orca presets and documentation.

## Main changes compared with the older GitHub v1.01 export

- Pure-Python workflow; no Z-Suite/g2z.jar required at normal runtime.
- Added the critical base file `g2z_wrapper_orca_base_lab14_known_good.py`.
- Updated Orca presets to `v1.4.14_current_converter`.
- Temperature policy: `ORCA_OVERRIDES_ZSUITE_DEFAULTS`.
- `CHAMBER=AUTO`, `T0_TEMP=AUTO`, `T1_TEMP=AUTO`.
- `E_SPEED_SCALE=AUTO`, `RETRACT_SPEED_SCALE=AUTO`.
- Smart restore in DUAL layer-clean.
- Safe single T0 clean without dual load context.
- Confirmed dual T1→T0 clean behavior matching Z-Suite logic.
- Canonical profile suffix policy for user-renamed presets.
- Fan `M106 S` clamp to `0..255`.
- Optional `;ZORTRAX_LOAD_FILAMENT` marker.

## v1.4.16 — optional marker

```gcode
;ZORTRAX_LOAD_FILAMENT T0
;ZORTRAX_LOAD_FILAMENT T1
;ZORTRAX_LOAD_FILAMENT BOTH
;ZORTRAX_LOAD_FILAMENT AUTO
```

The marker is off by default and is intended for deliberate pre-print/load-like use above the waste bin. It does not replace normal `TOOLCHANGE_CLEAN`.

## Warnings

- This is a reverse-engineering project for classic `.zcode`.
- Start with short test prints.
- Do not mix files from different versions.
- For single mode, leave Tool change / Change filament G-code empty.
- In Filament Advanced, add only diagnostic `ZORTRAX_FILAMENT_PROFILE` comments, not real motion or temperature commands.
