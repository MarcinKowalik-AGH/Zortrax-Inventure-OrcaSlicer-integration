# Zortrax Inventure / Orca — latest material, purge, raft and speed database update

Date: 2026-05-03

This file is included in the v1.2.9 and v1.4.1 packages. It consolidates the current state from the latest chat.

## Core rules preserved

- `E_SPEED_SCALE` and `RETRACT_SPEED_SCALE` scale **feedrate F only**, not E length.
- `SKIP_AFTER_TOOLCHANGE=1` remains mandatory so `LAYER_CLEAN` does not immediately duplicate `TOOLCHANGE_CLEAN` purge/clean.
- Bin/waste purge-clean over the bucket is not printed tower geometry.
- Orca `prime tower` may be mapped conceptually to Z-Suite `cooling tower`; this is separate from waste-bin purge.
- `OP0E` and `OP16` match chamber temperature values in the analyzed files, not per-feature acceleration.
- No classic `.zcode` per-feature acceleration table has been found; Orca accelerations remain safe proposals.

## Confirmed dual T0 clean fix

```text
E -20 area F3
RESTORE E0
SELECT T0
POS 00
F480  E+21.000 area F4
F2000 E+22.000 area FE
DWELL 3000
clean path: 0A -> 08 -> 09 -> 07 -> 0A -> 08 -> 00
F2000 E+21.000 area FD
RESTORE E0
```

`LAYER_CLEAN T0` in dual uses the same clean body but without old-tool retract and without SELECT.

## Material code updates

### Native / Z-materials observed or maintained

- `Z-ABS` legacy/native observed as `0x00`.
- `Z-ULTRAT=0x01`, `Z-GLASS=0x02`, `Z-PETG=0x05`, `Z-PLA=0x0A`, `Z-PLA Pro=0x0B`, `Z-ASA Pro=0x0C`, `Z-FLEX=0x0F`, `Z-NYLON=0x10` are confirmed from `w.zip` native singles.
- `Z-SUPPORT Premium=0x11` is confirmed as real support in dual.
- Existing map still keeps `Z-HIPS=0x03`, `Z-PCABS=0x04`, `Z-ULTRAT Plus=0x06`, `Z-SUPPORT=0x07`, `Z-ESD=0x08`, `Z-PHA=0x09`, `Z-SUPPORT Plus=0x0D`, `Z-SemiFlex=0x0E`, `Z-PEEK=0x12` pending full profile samples.

### External header codes now observed

- `ABS-based=0x81`
- `PETG-based=0x83`
- `GLASS-type=0x84`
- `PLA-based=0x86`
- `FLEX-based=0x87`
- `NYLON-based=0x89`
- `ULTRAT-based=0x91`
- `ESD PETG-based=0x92`
- `PLA Pro-based=0x94`
- `ASA Pro-based=0x95`
- `SEMIFLEX-based=0x96`

## Raft/brim rules

- Raft ON removes brim: no area `0x22`.
- `byte72 = effective raft` in the observed native Z-Suite samples.
- Negative raft layers are `-(effective+1)..-1`.
- Single observed pattern: `0x0A x2`, `0x0B x1`, `0x0C x1` for effective 4; `0x0C x2` for observed effective >= 6; rest `0x0D`.
- Dual observed pattern: `0x0A x2`, `0x0B x1`, `0x0C x1`, rest `0x0D`.

## Missing full native samples

Still needed for full material/profile closure:

```text
Z-HIPS
Z-PCABS
Z-ULTRAT Plus
Z-ESD
Z-PHA
Z-SemiFlex native
Z-PEEK
Z-SUPPORT as real dual support
Z-SUPPORT Plus as real dual support
BVOH/BASF as real support
```


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
