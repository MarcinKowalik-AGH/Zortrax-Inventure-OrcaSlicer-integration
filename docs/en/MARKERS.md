# `ZORTRAX_*` G-code markers

The converter uses special comments as high-level commands. Orca keeps them in G-code, and `g2z_wrapper_orca.py` converts them to Zortrax-specific classic ZCode sequences.

## `;ZORTRAX_START_MACHINE`

```gcode
;ZORTRAX_START_MACHINE AUTO
```

Modes:

| Mode | Meaning |
|---|---|
| `AUTO` | detect single/dual from metadata and active tools |
| `SINGLE` | force single start sequence |
| `DUAL` | force dual start sequence |

It performs a Z-Suite-like startup sequence, including homing XY and Z.

## `;ZORTRAX_START_PURGE`

```gcode
;ZORTRAX_START_PURGE AUTO LENGTH=30
;ZORTRAX_START_PURGE SINGLE LENGTH=30
;ZORTRAX_START_PURGE DUAL LENGTH=30
```

In v1.01 this marker performs **purge only**:

- material amount is taken from `LENGTH=...`,
- no retract is added,
- before purge, the selected extruder is heated to the material temperature from Orca metadata.

## `;ZORTRAX_SPECIAL_CLEAN`

```gcode
;ZORTRAX_SPECIAL_CLEAN AUTO
```

Modes:

| Mode | Meaning |
|---|---|
| `AUTO` | clean according to toolchange metadata and active tool |
| `SINGLE` | single-head cleaning path |
| `DUAL` | full dual cleaning path |
| `T0` | clean model nozzle only |
| `T1` | clean support nozzle only |

## `;ZORTRAX_TOOLCHANGE_META`

Passes Orca toolchange placeholder values to the converter.

Example:

```gcode
;ZORTRAX_TOOLCHANGE_META PREV=0 NEXT=1 LAYER=12 FLUSH=35 OLD_RETRACT=5 NEW_RETRACT=5
```

Important fields:

| Field | Meaning |
|---|---|
| `PREV` / `previous_extruder` | previous tool |
| `NEXT` / `next_extruder` | next tool |
| `LAYER` / `layer_num` | layer number |
| `FLUSH` / `flush_length` | Orca flush amount |
| `OLD_RETRACT`, `NEW_RETRACT` | retract/deretract lengths |
| `OLD_E_F`, `NEW_E_F` | extruder feedrates |
| `X`, `Y`, `Z` | return position after toolchange |

## `;ZORTRAX_END_MACHINE`

```gcode
;ZORTRAX_END_MACHINE AUTO
```

Generates the end sequence for the selected single/dual mode.
