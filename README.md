# Zortrax Inventure + OrcaSlicer integration

**Current GitHub export:** `v1.4.16`  
**Converter:** `v1.4.16-production-load-filament-marker-2026-05-06`  
**Base converter:** `v1.4.16-base-LAB38-safe-load-filament-marker-2026-05-06`  
**Orca presets:** `v1.4.14_current_converter`  
**Export date:** `2026-05-08`

This project enables generating classic `.zcode` files for **Zortrax Inventure** directly from **OrcaSlicer** with a pure-Python post-processing converter. It is intended to reproduce the most important Z-Suite behavior: `.zcode` header fields, material IDs, single/dual jobs, support handling, start routines, bin purge/clean, toolchange cleaning, raft/seam/tower semantics and selected firmware-facing metadata.

> This is a reverse-engineering project. Use short test prints first and do not treat experimental material entries as fully validated.

## What is included

```text
converter/       Pure-Python converter and Windows/macOS launchers
orca_presets/    Current Orca printer/process/filament preset bundles
docs/            Installation, Machine G-code, materials and troubleshooting notes
examples/        Ready-to-copy Machine G-code snippets
source_context/  Consolidated project source/transfer notes
reports/         Self-check/reference reports where available
```

## Important installation rule

Always replace **both** Python files together:

```text
converter/g2z_wrapper_orca.py
converter/g2z_wrapper_orca_base_lab14_known_good.py
```

Replacing only `g2z_wrapper_orca.py` is not enough, because the wrapper delegates the mechanical conversion to the base file.

## Quick installation

Windows:

```text
Copy converter/* to C:\Users\<USER>\OrcaScripts\
Set Orca post-processing script to:
C:\Users\<USER>\OrcaScripts\run_g2z_orca_postprocess.bat
```

macOS:

```bash
mkdir -p ~/OrcaScripts
cp converter/* ~/OrcaScripts/
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.sh
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.command
```

Set Orca post-processing script to:

```text
/Users/<username>/OrcaScripts/run_g2z_orca_postprocess.command
```

## Recommended Machine G-code

See:

```text
docs/en/MACHINE_GCODE.md
docs/pl/MACHINE_GCODE_PL.md
```

## Key features in v1.4.16

- Pure-Python G-code → classic `.zcode` conversion.
- Current Orca single/dual presets.
- `CHAMBER=AUTO`, `T0_TEMP=AUTO`, `T1_TEMP=AUTO` temperature policy.
- `E_SPEED_SCALE=AUTO` and `RETRACT_SPEED_SCALE=AUTO` for converter-generated technical moves.
- Smart DUAL layer-clean restore inherited from v1.4.15.
- Safe single T0 clean and confirmed dual T1→T0 clean behavior.
- M83/relative E handling through Orca-like M82 conversion.
- OP02/process-speed documentation.
- M106 fan clamp to `0..255`.
- Optional `;ZORTRAX_LOAD_FILAMENT` marker for a deliberate pre-print/load-like routine above the bin.

## Documentation index

- Polish README: [`README_PL.md`](README_PL.md)
- Installation: [`docs/en/INSTALL.md`](docs/en/INSTALL.md), [`docs/pl/INSTALL_PL.md`](docs/pl/INSTALL_PL.md)
- Release notes: [`docs/en/RELEASE_NOTES.md`](docs/en/RELEASE_NOTES.md), [`docs/pl/RELEASE_NOTES_PL.md`](docs/pl/RELEASE_NOTES_PL.md)
- Troubleshooting: [`docs/en/TROUBLESHOOTING.md`](docs/en/TROUBLESHOOTING.md), [`docs/pl/TROUBLESHOOTING_PL.md`](docs/pl/TROUBLESHOOTING_PL.md)
