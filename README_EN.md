# Zortrax Inventure + OrcaSlicer integration


This project provides OrcaSlicer profiles and a post-processing converter for producing `.zcode` files for the **Zortrax Inventure** printer without using Z-Suite as the slicer.

Current package: **v1.01**.

### Repository contents

```text
scripts/
  g2z_wrapper_orca.py                 # main G-code -> classic .zcode converter
  run_g2z_orca_postprocess.bat        # Windows launcher for Orca post-processing
  run_g2z_orca_postprocess.sh         # macOS/Linux launcher
  run_g2z_orca_postprocess.command    # thin macOS launcher calling the .sh script

presets/
  Zortrax Inventure 0.4 nozzle - dual.orca_printer
  Zortrax Inventure 0.4 nozzle - single.orca_printer

docs/pl/                              # Polish documentation
docs/en/                              # English documentation
examples/                             # example Machine G-code and post-processing paths
```

### Pipeline

1. OrcaSlicer generates G-code and metadata/comments.
2. Orca runs the post-processing launcher.
3. The launcher starts `scripts/g2z_wrapper_orca.py`.
4. The converter reads the G-code, the `ORCA METADATA` block, comment fallbacks, and `;ZORTRAX_*` markers.
5. The converter generates classic `.zcode`, fills the Inventure header fields, and recalculates the header CRC.
6. The resulting `.zcode` is saved to the final Save/Save As location provided by Orca, or to the path passed through `--output` when run manually.

### Key technical decisions in v1.01

- The active workflow is **pure Python**: no Java and no `g2z.jar`.
- For Orca `.gcode.pp` files, the converter requires Orca's output path from the environment; it does not use the old `out` fallback directory.
- Launchers prefer `~/OrcaScripts` / `%USERPROFILE%\OrcaScripts`; if the wrapper is not found there, they use the launcher directory.
- In v1.01, `;ZORTRAX_START_PURGE ... LENGTH=...` performs purge only, using the `LENGTH` value, with no retract. The extruder is heated to the material temperature from Orca metadata before the purge.
- The profiles include two printer variants: `single` and `dual`, with separate process profiles and a shared filament family.

### Quick installation

1. Copy the `scripts/` directory to `OrcaScripts` in your home directory:
   - Windows: `C:\Users\<user>\OrcaScripts\`
   - macOS: `/Users/<user>/OrcaScripts/`
2. Import the required OrcaSlicer profile from `presets/`:
   - `Zortrax Inventure 0.4 nozzle - single.orca_printer`
   - `Zortrax Inventure 0.4 nozzle - dual.orca_printer`
3. Set Orca's post-processing script to the full launcher path:
   - Windows: `C:\Users\<user>\OrcaScripts\run_g2z_orca_postprocess.bat`
   - macOS: `/Users/<user>/OrcaScripts/run_g2z_orca_postprocess.command`
4. Slice / Export plate from Orca. The result should be saved as `.zcode` in the selected Save/Save As location.

Details: [`docs/en/INSTALLATION.md`](docs/en/INSTALLATION.md).

### How to upload this project to GitHub

The simplest method is to create an empty repository on GitHub, unpack this package locally, and run:

```bash
git init
git add .
git commit -m "Initial Zortrax Inventure OrcaSlicer integration v1.01"
git branch -M main
git remote add origin https://github.com/<your-login>/zortrax-inventure-orca.git
git push -u origin main
git tag v1.01
git push origin v1.01
```

Full guide: [`docs/en/GITHUB_PUBLISHING.md`](docs/en/GITHUB_PUBLISHING.md).

### Warning

This is a reverse-engineering project based on practical tests. Before long or expensive prints, run a short test with a simple model and verify homing, heating, purge, and toolchange behavior.
