# Zortrax Inventure + OrcaSlicer integration / Integracja Zortrax Inventure z OrcaSlicer

## Polski

Projekt zawiera konfiguracje OrcaSlicer oraz konwerter post-processingu umożliwiający przygotowanie plików `.zcode` dla drukarki **Zortrax Inventure** bez używania Z-Suite jako slicera.

Aktualna paczka: **v1.01**.

### Co zawiera repozytorium

```text
scripts/
  g2z_wrapper_orca.py                 # główny konwerter G-code -> classic .zcode
  run_g2z_orca_postprocess.bat        # launcher Windows dla Orca post-processing
  run_g2z_orca_postprocess.sh         # launcher macOS/Linux
  run_g2z_orca_postprocess.command    # cienki launcher macOS uruchamiający .sh

presets/
  Zortrax Inventure 0.4 nozzle - dual.orca_printer
  Zortrax Inventure 0.4 nozzle - single.orca_printer

docs/pl/                              # dokumentacja po polsku
docs/en/                              # documentation in English
examples/                             # przykładowe pola G-code i ścieżki post-processingu
```

### Pipeline

1. OrcaSlicer generuje G-code oraz komentarze/metadane.
2. Orca uruchamia launcher post-processingu.
3. Launcher uruchamia `scripts/g2z_wrapper_orca.py`.
4. Konwerter czyta G-code, blok `ORCA METADATA`, fallbacki z komentarzy oraz markery `;ZORTRAX_*`.
5. Konwerter generuje classic `.zcode`, ustawia pola nagłówka Inventure i przelicza CRC.
6. Wynikowy `.zcode` trafia do finalnej lokalizacji Save/Save As przekazanej przez Orca albo do lokalizacji podanej przez `--output` przy ręcznym uruchomieniu.

### Najważniejsze decyzje techniczne v1.01

- Aktywny workflow jest **pure Python**: bez Javy i bez `g2z.jar`.
- Dla plików Orca `.gcode.pp` konwerter wymaga ścieżki wyjściowej z environment Orca; nie używa starego fallbacku `out`.
- Launchery preferują katalog `~/OrcaScripts` / `%USERPROFILE%\OrcaScripts`, a jeśli nie znajdą tam wrappera, użyją katalogu launchera.
- `;ZORTRAX_START_PURGE ... LENGTH=...` w v1.01 wykonuje wyłącznie purge o długości `LENGTH`, bez retrakcji. Ekstruder jest przed purge nagrzewany do temperatury materiału z metadanych Orca.
- W presetach są dwa warianty drukarki: `single` i `dual`, z osobnymi processami, ale wspólną rodziną filamentów.

### Szybka instalacja

1. Skopiuj katalog `scripts/` do `OrcaScripts` w katalogu domowym:
   - Windows: `C:\Users\<użytkownik>\OrcaScripts\`
   - macOS: `/Users/<użytkownik>/OrcaScripts/`
2. Zaimportuj w OrcaSlicer odpowiedni preset z katalogu `presets/`:
   - `Zortrax Inventure 0.4 nozzle - single.orca_printer`
   - `Zortrax Inventure 0.4 nozzle - dual.orca_printer`
3. W Orca ustaw post-processing script na pełną ścieżkę do launchera:
   - Windows: `C:\Users\<użytkownik>\OrcaScripts\run_g2z_orca_postprocess.bat`
   - macOS: `/Users/<użytkownik>/OrcaScripts/run_g2z_orca_postprocess.command`
4. Slice / Export plate w Orca. Wynik powinien zostać zapisany jako `.zcode` w lokalizacji Save/Save As.

Szczegóły: [`docs/pl/INSTALLATION.md`](docs/pl/INSTALLATION.md).



### Ostrzeżenie

To jest projekt reverse-engineeringowy oparty na ustaleniach testowych. Przed długimi lub kosztownymi wydrukami wykonaj krótki test na prostym modelu i sprawdź homing, nagrzewanie, purge oraz toolchange.

---

## English

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



### Warning

This is a reverse-engineering project based on practical tests. Before long or expensive prints, run a short test with a simple model and verify homing, heating, purge, and toolchange behavior.
