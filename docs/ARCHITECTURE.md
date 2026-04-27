# Architektura rozwiązania

## Warstwy projektu

1. **Preset Orca** (`presets/*.orca_printer`)
   - definiuje drukarkę, procesy, filamenty i Machine G-code,
   - wstawia markery `ZORTRAX_*`, które są później interpretowane przez konwerter.

2. **Launcher systemowy** (`scripts/run_g2z_orca_postprocess.*`)
   - jest wskazywany w Orca jako post-processing script,
   - znajduje właściwy `g2z_wrapper_orca.py`,
   - uruchamia Pythona w trybie niebuforowanym,
   - ustawia ścieżkę logu.

3. **Konwerter** (`scripts/g2z_wrapper_orca.py`)
   - czyta G-code,
   - czyta `ORCA METADATA`, fallbacki z komentarzy i markery `ZORTRAX_*`,
   - generuje binarny strumień classic ZCode,
   - buduje i patchuje nagłówek,
   - przelicza CRC,
   - zapisuje plik `.zcode`.

4. **Drukarka**
   - otrzymuje plik `.zcode`,
   - wykonuje sekwencje start/clean/end zbliżone do Z-Suite.

## Przepływ danych

```text
Orca preset
   ↓
Machine G-code + Change filament G-code + ORCA METADATA
   ↓
run_g2z_orca_postprocess.bat/.sh/.command
   ↓
g2z_wrapper_orca.py
   ↓
classic .zcode dla Zortrax Inventure
```

## Główne zasady projektu

- Nie używać `g2z.jar` w aktywnym workflow.
- Nie używać Javy w aktywnym workflow.
- Nie zapisywać automatycznie plików z Orca do starego katalogu `out`.
- Nie opierać startu na zwykłym `G28`, tylko na `;ZORTRAX_START_MACHINE AUTO`.
- Nie dodawać retrakcji do `START_PURGE`; w v1.01 ma to być tylko purge z `LENGTH`.
- Prędkości, temperatury i długości purge/retract mają pochodzić z metadanych Orca, jeżeli są dostępne.
