# Solution architecture

## Layers

1. **Orca profile** (`presets/*.orca_printer`)
   - defines printer, process profiles, filament profiles, and Machine G-code,
   - inserts `ZORTRAX_*` markers for the converter.

2. **System launcher** (`scripts/run_g2z_orca_postprocess.*`)
   - is selected in Orca as post-processing script,
   - finds `g2z_wrapper_orca.py`,
   - starts Python in unbuffered mode,
   - sets the log path.

3. **Converter** (`scripts/g2z_wrapper_orca.py`)
   - reads G-code,
   - reads `ORCA METADATA`, fallback comments, and `ZORTRAX_*` markers,
   - generates binary classic ZCode,
   - patches the header,
   - recalculates CRC,
   - writes `.zcode`.

4. **Printer**
   - receives `.zcode`,
   - executes Z-Suite-like start, purge, clean, and end sequences.

## Data flow

```text
Orca preset
   ↓
Machine G-code + Change filament G-code + ORCA METADATA
   ↓
run_g2z_orca_postprocess.bat/.sh/.command
   ↓
g2z_wrapper_orca.py
   ↓
classic .zcode for Zortrax Inventure
```

## Rules

- Do not use `g2z.jar` in the active workflow.
- Do not use Java in the active workflow.
- Do not silently save Orca jobs to the old `out` directory.
- Prefer `;ZORTRAX_START_MACHINE AUTO` over plain `G28`.
- `START_PURGE` in v1.01 must be purge-only and use `LENGTH`.
