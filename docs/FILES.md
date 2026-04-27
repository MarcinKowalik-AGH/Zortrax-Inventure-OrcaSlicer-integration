# Opis plików repozytorium

## `scripts/g2z_wrapper_orca.py`

Główny konwerter pure Python. Przyjmuje G-code z Orca i generuje classic `.zcode` dla Zortrax Inventure.

Najważniejsze zadania:

- czyta blok `ORCA METADATA`, jeżeli występuje,
- czyta fallbacki z komentarzy Orca, np. czas wydruku, długości filamentów, typy filamentów,
- interpretuje markery `;ZORTRAX_START_MACHINE`, `;ZORTRAX_START_PURGE`, `;ZORTRAX_SPECIAL_CLEAN`, `;ZORTRAX_TOOLCHANGE_META`, `;ZORTRAX_SPECIAL_POS`, `;ZORTRAX_END_MACHINE`,
- generuje strumień komend classic ZCode,
- ustawia potwierdzone pola nagłówka Inventure,
- przelicza CRC nagłówka,
- zapisuje log w `orca_postprocess_last.log` albo w pliku wskazanym przez `G2Z_LOG_FILE`.

Opcje CLI:

```text
g2z_wrapper_orca.py [input_file]
g2z_wrapper_orca.py -i input.gcode -o output.zcode
```

Dostępne opcje:

| Opcja | Znaczenie |
|---|---|
| `input_file` | wejściowy G-code przekazany pozycyjnie, typowo przez Orca post-processing |
| `-i`, `--input` | wejściowy G-code, alternatywa dla argumentu pozycyjnego |
| `-o`, `--output` | ręczne wskazanie pliku wynikowego `.zcode` |
| `-d`, `--device` | identyfikator urządzenia, domyślnie `INVENTURE` |
| `--software-version` | wersja wpisywana w nagłówek, domyślnie `2.32.0.0` |
| `-l`, `--log` | uruchamia raportowanie/logowanie |
| `--dump-meta` | wypisuje zparsowane metadane jako JSON |
| `--keep-work` | zachowuje tymczasową kopię roboczą G-code po normalizacji/konwersji |

## `scripts/run_g2z_orca_postprocess.bat`

Launcher Windows dla pola **Post-processing scripts** w Orca.

Robi następujące rzeczy:

- wykrywa katalog użytkownika z `USERPROFILE`, `HOMEDRIVE`+`HOMEPATH` albo `HOME`,
- preferuje `%USERPROFILE%\OrcaScripts\g2z_wrapper_orca.py`,
- jeśli wrappera nie ma w katalogu domowym, używa katalogu launchera,
- szuka Pythona przez `py -3 -u`, a potem `python -u`,
- ustawia `G2Z_LOG_FILE`, `PYTHONUNBUFFERED=1` i `G2Z_PROGRESS_STYLE=plain`,
- uruchamia wrapper i pokazuje wynik w konsoli.

## `scripts/run_g2z_orca_postprocess.sh`

Launcher macOS/Linux. Odpowiednik pliku `.bat`.

Robi następujące rzeczy:

- preferuje `$HOME/OrcaScripts/g2z_wrapper_orca.py`,
- jeśli wrappera nie ma w katalogu domowym, używa katalogu launchera,
- szuka Pythona w typowych ścieżkach Homebrew i systemowych,
- ustawia `G2Z_LOG_FILE`, `PYTHONUNBUFFERED=1` i `G2Z_PROGRESS_STYLE=plain`,
- uruchamia wrapper w trybie niebuforowanym.

## `scripts/run_g2z_orca_postprocess.command`

Cienki launcher macOS. Orca może wskazywać ten plik w polu post-processingu, a on uruchamia `run_g2z_orca_postprocess.sh` z tymi samymi argumentami.

## `presets/Zortrax Inventure 0.4 nozzle - dual.orca_printer`

Bundle Orca dla trybu dual.

Zawiera:

- drukarkę `Zortrax Inventure 0.4 nozzle - dual`,
- 4 processy: `0.08mm Ultra Quality`, `0.15mm Quality`, `0.20mm Standard`, `0.30mm Draft`,
- filaments natywne Zortrax, external oraz `BASF Ultrafuse BVOH`,
- start G-code:

```gcode
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE DUAL LENGTH=30
```

- change filament G-code z `ZORTRAX_TOOLCHANGE_META` i `ZORTRAX_SPECIAL_CLEAN AUTO 5 PURGE=AUTO IDLE_RETRACT=AUTO`,
- end G-code:

```gcode
;ZORTRAX_END_MACHINE AUTO
```

Domyślny proces: `0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual`.
Domyślne filamenty: `Z-PLA`, `Z-SUPPORT`.

## `presets/Zortrax Inventure 0.4 nozzle - single.orca_printer`

Bundle Orca dla trybu single.

Zawiera:

- drukarkę `Zortrax Inventure 0.4 nozzle - single`,
- 4 processy: `0.08mm Ultra Quality`, `0.15mm Quality`, `0.20mm Standard`, `0.30mm Draft`,
- tę samą rodzinę filamentów co dual,
- start G-code:

```gcode
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE SINGLE LENGTH=20
```

- pusty change filament G-code,
- end G-code:

```gcode
;ZORTRAX_END_MACHINE AUTO
```

Domyślny proces: `0.15mm Quality @Zortrax Inventure 0.4 nozzle - single`.
Domyślny filament: `Z-PLA`.
