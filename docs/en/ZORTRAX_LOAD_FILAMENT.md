# ZORTRAX_LOAD_FILAMENT — v1.4.16

Optional marker for deliberately triggering a shortened, printer-confirmed load-like routine above the waste bin. It is not part of START_MACHINE by default.

## Syntax

```gcode
;ZORTRAX_LOAD_FILAMENT T0
;ZORTRAX_LOAD_FILAMENT T1
;ZORTRAX_LOAD_FILAMENT BOTH
;ZORTRAX_LOAD_FILAMENT AUTO
```

Options:

```text
PARK=1/0          default 1; parks T0 on 09, T1 on 0A
POST_RESTORE=1/0  default 1; adds RESTORE E0 after parking
TEMP=AUTO/OFF     default AUTO; uses Orca temperatures, OFF skips temp commands
T0_TEMP=...       manual T0 override
T1_TEMP=...       manual T1 override
STANDBY_TEMP=...  manual shallow standby override for inactive tool
```

## AUTO

- SINGLE -> T0
- DUAL -> T0 then T1

## Important

This procedure intentionally keeps the confirmed trigger behavior: after the technical -20 mm retract of the old tool, there is no immediate RESTORE E0. The final sequence includes RESTORE, park and an extra RESTORE after parking.

Do not use this as a replacement for normal TOOLCHANGE_CLEAN. It is an optional pre-print/load marker for deliberate use.
