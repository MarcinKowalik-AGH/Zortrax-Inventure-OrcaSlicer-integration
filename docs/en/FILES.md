# Repository file description

## `scripts/g2z_wrapper_orca.py`

Main pure-Python converter. It accepts Orca G-code and generates classic `.zcode` for Zortrax Inventure.

Main tasks:

- reads `ORCA METADATA`, if present,
- reads fallback Orca comments such as print time, filament length, and filament type,
- interprets `;ZORTRAX_START_MACHINE`, `;ZORTRAX_START_PURGE`, `;ZORTRAX_SPECIAL_CLEAN`, `;ZORTRAX_TOOLCHANGE_META`, `;ZORTRAX_SPECIAL_POS`, and `;ZORTRAX_END_MACHINE`,
- generates the classic ZCode command stream,
- sets confirmed Inventure header fields,
- recalculates the header CRC,
- writes logs to `orca_postprocess_last.log` or to the file selected by `G2Z_LOG_FILE`.

CLI examples:

```text
g2z_wrapper_orca.py [input_file]
g2z_wrapper_orca.py -i input.gcode -o output.zcode
```

Options:

| Option | Meaning |
|---|---|
| `input_file` | input G-code passed positionally, usually by Orca post-processing |
| `-i`, `--input` | input G-code, alternative to the positional argument |
| `-o`, `--output` | manually selected output `.zcode` path |
| `-d`, `--device` | device identifier, default `INVENTURE` |
| `--software-version` | version written to the header, default `2.32.0.0` |
| `-l`, `--log` | enables logging/reporting |
| `--dump-meta` | prints parsed metadata as JSON |
| `--keep-work` | keeps the temporary normalized/converted G-code work copy |

## Launchers

### `scripts/run_g2z_orca_postprocess.bat`

Windows launcher for Orca's **Post-processing scripts** field. It finds Python, finds `g2z_wrapper_orca.py`, sets log/progress environment variables, and runs the converter.

### `scripts/run_g2z_orca_postprocess.sh`

macOS/Linux launcher. It prefers `$HOME/OrcaScripts/g2z_wrapper_orca.py`, falls back to the launcher directory, finds Python, and runs the converter.

### `scripts/run_g2z_orca_postprocess.command`

Thin macOS launcher that calls `run_g2z_orca_postprocess.sh` with the same arguments.

## Presets

### `presets/Zortrax Inventure 0.4 nozzle - dual.orca_printer`

Bundle for dual mode. It contains the dual printer profile, process profiles, native and external filament profiles, and machine G-code using `ZORTRAX_*` markers.

### `presets/Zortrax Inventure 0.4 nozzle - single.orca_printer`

Bundle for single mode. It keeps the same process family where possible, but disables support filament assignments that belong to dual mode.

## `examples/`

Contains example Machine G-code and example post-processing paths for Windows and macOS.
