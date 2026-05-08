# Installation — Windows and macOS

## 1. Import Orca presets

Import the current presets from:

```text
orca_presets/
```

Important files:

```text
Zortrax Inventure 0.4 nozzle - single_v1.4.14_current_converter.orca_printer
Zortrax Inventure 0.4 nozzle - dual_v1.4.14_current_converter.orca_printer
```

You can also use the bundled preset ZIP if Orca imports it correctly.

## 2. Converter installation

Copy all files from `converter/` to your Orca scripts directory.

### Windows

Recommended folder:

```text
C:\Users\<USER>\OrcaScripts\
```

Example:

```text
C:\Users\Marcin Kowalik\OrcaScripts\
```

Copy:

```text
g2z_wrapper_orca.py
g2z_wrapper_orca_base_lab14_known_good.py
run_g2z_orca_postprocess.bat
```

In OrcaSlicer → Printer settings → Others → Post-processing scripts set:

```text
C:\Users\<USER>\OrcaScripts\run_g2z_orca_postprocess.bat
```

### macOS

Recommended folder:

```text
/Users/<username>/OrcaScripts/
```

Commands:

```bash
mkdir -p ~/OrcaScripts
cp converter/* ~/OrcaScripts/
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.sh
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.command
```

In OrcaSlicer → Printer settings → Others → Post-processing scripts set:

```text
/Users/<username>/OrcaScripts/run_g2z_orca_postprocess.command
```

## 3. Critical update rule

Always replace these files together:

```text
g2z_wrapper_orca.py
g2z_wrapper_orca_base_lab14_known_good.py
```

Do not mix an old wrapper with a new base file or the opposite.

## 4. First test

1. Choose a small simple model.
2. Use the single or dual profile from this package.
3. Generate the file through Orca post-processing.
4. Check that a `.zcode` file was created.
5. Start with a short control print.
