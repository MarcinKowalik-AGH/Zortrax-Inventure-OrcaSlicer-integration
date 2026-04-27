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

