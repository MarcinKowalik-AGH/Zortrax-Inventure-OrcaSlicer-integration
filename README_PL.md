# Zortrax Inventure + OrcaSlicer integration

**Aktualny eksport GitHub:** `v1.4.16`  
**Konwerter:** `v1.4.16-production-load-filament-marker-2026-05-06`  
**Konwerter bazowy:** `v1.4.16-base-LAB38-safe-load-filament-marker-2026-05-06`  
**Presety Orca:** `v1.4.14_current_converter`  
**Data eksportu:** `2026-05-08`

Projekt umożliwia przygotowywanie klasycznych plików `.zcode` dla **Zortrax Inventure** bezpośrednio z **OrcaSlicer**, z użyciem konwertera post-process w pure Python. Celem jest jak najwierniejsze odtworzenie kluczowego zachowania Z-Suite: pól nagłówka `.zcode`, kodów materiałów, trybów single/dual, obsługi supportu, procedur startu, purge/clean nad koszem, toolchange-clean, semantyki raft/seam/tower oraz wybranych metadanych potrzebnych firmware Inventure.

> To projekt reverse engineeringu. Najpierw testować krótkie wydruki i ostrożnie traktować wpisy eksperymentalne.

## Co zawiera paczka

```text
converter/       Konwerter pure Python i launchery Windows/macOS
orca_presets/    Aktualne presety Orca single/dual
_docs/           Nie używane — dokumentacja jest w docs/
docs/            Instalacja, Machine G-code, materiały, troubleshooting
examples/        Gotowe fragmenty Machine G-code do kopiowania
source_context/  Skonsolidowane źródła i brief transferowy
reports/         Raporty self-check / referencyjne, jeśli są dostępne
```

## Najważniejsza zasada instalacji

Zawsze podmieniaj **oba** pliki Python razem:

```text
converter/g2z_wrapper_orca.py
converter/g2z_wrapper_orca_base_lab14_known_good.py
```

Sama podmiana `g2z_wrapper_orca.py` nie wystarczy, bo właściwa mechaniczna konwersja idzie przez plik bazowy.

## Szybka instalacja

Windows:

```text
Skopiuj converter/* do C:\Users\<USER>\OrcaScripts\
W Orca ustaw post-processing script:
C:\Users\<USER>\OrcaScripts\run_g2z_orca_postprocess.bat
```

macOS:

```bash
mkdir -p ~/OrcaScripts
cp converter/* ~/OrcaScripts/
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.sh
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.command
```

W Orca ustaw post-processing script:

```text
/Users/<username>/OrcaScripts/run_g2z_orca_postprocess.command
```

## Zalecane Machine G-code

Zobacz:

```text
docs/pl/MACHINE_GCODE_PL.md
docs/en/MACHINE_GCODE.md
```

## Najważniejsze zmiany v1.4.16

- Konwerter pure Python G-code → classic `.zcode`.
- Aktualne presety Orca single/dual.
- Polityka temperatur `CHAMBER=AUTO`, `T0_TEMP=AUTO`, `T1_TEMP=AUTO`.
- `E_SPEED_SCALE=AUTO` i `RETRACT_SPEED_SCALE=AUTO` dla technicznych ruchów generowanych przez konwerter.
- Smart restore w DUAL layer-clean z linii v1.4.15.
- Bezpieczne single T0 clean i potwierdzone dual T1→T0 clean.
- Obsługa M83/relative E przez kopię roboczą Orca-like M82.
- Dokumentacja OP02/process-speed.
- Clamp `M106 S` do zakresu `0..255`.
- Opcjonalny marker `;ZORTRAX_LOAD_FILAMENT` do świadomie wywoływanej procedury pre-print/load-like nad koszem.

## Indeks dokumentacji

- English README: [`README.md`](README.md)
- Instalacja: [`docs/pl/INSTALL_PL.md`](docs/pl/INSTALL_PL.md), [`docs/en/INSTALL.md`](docs/en/INSTALL.md)
- Release notes: [`docs/pl/RELEASE_NOTES_PL.md`](docs/pl/RELEASE_NOTES_PL.md), [`docs/en/RELEASE_NOTES.md`](docs/en/RELEASE_NOTES.md)
- Troubleshooting: [`docs/pl/TROUBLESHOOTING_PL.md`](docs/pl/TROUBLESHOOTING_PL.md), [`docs/en/TROUBLESHOOTING.md`](docs/en/TROUBLESHOOTING.md)
