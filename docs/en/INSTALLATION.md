# Installation

## Requirements

- OrcaSlicer 2.3.x / 2.4.x or a compatible version producing similar metadata.
- Python 3 available in the operating system.
- Zortrax Inventure using classic `.zcode` files.

The active v1.01 workflow does **not** require Java and does **not** require `g2z.jar`.

## Windows

1. Create:

```text
C:\Users\<user>\OrcaScripts\
```

2. Copy these files from `scripts/`:

```text
g2z_wrapper_orca.py
run_g2z_orca_postprocess.bat
```

3. Import the `.orca_printer` preset from `presets/` in OrcaSlicer.

4. In Orca, set **Post-processing scripts** to:

```text
C:\Users\<user>\OrcaScripts\run_g2z_orca_postprocess.bat
```

5. Slice and export. The converter should create a `.zcode` file at Orca's final Save/Save As path.

## macOS

1. Create:

```text
/Users/<user>/OrcaScripts/
```

2. Copy these files from `scripts/`:

```text
g2z_wrapper_orca.py
run_g2z_orca_postprocess.sh
run_g2z_orca_postprocess.command
```

3. Make the launchers executable:

```bash
chmod +x /Users/<user>/OrcaScripts/run_g2z_orca_postprocess.sh
chmod +x /Users/<user>/OrcaScripts/run_g2z_orca_postprocess.command
```

4. Import the `.orca_printer` preset from `presets/` in OrcaSlicer.

5. Set **Post-processing scripts** to:

```text
/Users/<user>/OrcaScripts/run_g2z_orca_postprocess.command
```

## Recommended Machine G-code

Single:

```gcode
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE SINGLE LENGTH=30
```

Dual:

```gcode
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE DUAL LENGTH=30
```

Toolchange / filament change:

```gcode
;ZORTRAX_TOOLCHANGE_META PREV={previous_extruder} NEXT={next_extruder} LAYER={layer_num} FLUSH={flush_length}
;ZORTRAX_SPECIAL_CLEAN AUTO
```

End G-code:

```gcode
;ZORTRAX_END_MACHINE AUTO
```

## Manual diagnostic run

```bash
python3 scripts/g2z_wrapper_orca.py -i input.gcode -o output.zcode --log
```

Windows example:

```bat
py -3 scripts\g2z_wrapper_orca.py -i input.gcode -o output.zcode --log
```
