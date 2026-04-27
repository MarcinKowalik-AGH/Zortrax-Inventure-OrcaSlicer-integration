# Troubleshooting

## Orca does not create `.zcode`

Check:

1. Orca uses the full launcher path in the post-processing field.
2. `g2z_wrapper_orca.py` exists in `~/OrcaScripts` / `%USERPROFILE%\OrcaScripts`, or in the same directory as the launcher.
3. Python 3 is available.
4. A log file was created:
   - Windows: `orca_postprocess_last.log`,
   - macOS: `orca_postprocess.log`.

## Error: Orca output path is not available

For `.gcode.pp` files, the converter requires the final Save/Save As path from Orca. If it is missing, the converter exits with an error. This is intentional: v1.01 no longer writes to the old `out` directory.

Diagnostic workaround:

```bash
python3 scripts/g2z_wrapper_orca.py -i input.gcode -o output.zcode --log
```

## Unexpected homing behavior

Profiles should use:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

The converter protects plain `G28`, but Orca integration should still use `ZORTRAX_START_MACHINE`, because that marker emits the full Z-Suite-like start sequence.

## Material error on the printer

Check:

- whether `filament_t0` and `filament_t1` metadata match the actual materials,
- whether T1 is really support material in a dual job,
- whether the material mapping in `g2z_wrapper_orca.py` contains the material name,
- whether Z-SUPPORT family uses triplet `01 03 00`, and BASF BVOH uses `01 02 01`.

## `PURGE=AUTO` does nothing

`PURGE=AUTO` in toolchange depends on Orca metadata, especially `flush_length`. If Orca calculates `flush_length=0`, purge may be skipped.

Startup purge is independent and uses `LENGTH=...`:

```gcode
;ZORTRAX_START_PURGE DUAL LENGTH=30
```

## macOS does not show Terminal

This is expected. Current project decision: macOS can run silently in the background and diagnostics use the log file.
