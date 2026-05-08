# v1.4.13 — Orca profile suffix policy

This converter version allows user suffixes after canonical Orca profile names.

## Allowed examples

- `Z-PLA test` -> canonical `Z-PLA`
- `Z-SUPPORT ATP test` -> canonical `Z-SUPPORT ATP` when `;ZORTRAX_FILAMENT_PROFILE canonical=... zcode=...` is present
- `0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual test` -> canonical process prefix
- `Zortrax Inventure 0.4 nozzle - single copy` -> canonical printer prefix if printer metadata is present

## Required rule

The canonical/default name must stay at the beginning of the visible Orca preset name. Add your own text only after it.

Good:

```text
Z-PLA test
Z-PLA Marcin
0.15mm Quality @Zortrax Inventure 0.4 nozzle - single test
```

Bad:

```text
Test Z-PLA
My PLA based on Z-PLA
```

## Why

This lets you duplicate presets in Orca without changing default profiles, while the converter still maps material codes, process semantics and printer single/dual intent safely.

Filament mapping is strongest when the filament preset also contains:

```gcode
;ZORTRAX_FILAMENT_PROFILE name=... canonical=... zcode=... support_role=...
```

For process and printer names the rule is used as a tolerant canonical-prefix audit/fallback; motion generation remains driven by `ORCA METADATA`, `ZORTRAX_*` markers and confirmed converter logic.
