# Release notes — v1.4.16

## Status

Aktualizacja GitHub została przebudowana na bazie realnej paczki produkcyjnej:

```text
Zortrax_Inventure_Orca_PRODUCTION_v1.4.16_converter_configs_2026-05-06.zip
```

Ta wersja zawiera pełny konwerter, plik bazowy, launchery Windows/macOS, aktualne presety Orca oraz dokumentację.

## Najważniejsze zmiany względem wcześniejszego GitHub v1.01

- Przejście na pełny workflow pure Python, bez Z-Suite/g2z.jar w normalnym runtime.
- Dodanie drugiego, krytycznego pliku bazowego `g2z_wrapper_orca_base_lab14_known_good.py`.
- Aktualizacja presetów Orca do `v1.4.14_current_converter`.
- Polityka temperatur: `ORCA_OVERRIDES_ZSUITE_DEFAULTS`.
- `CHAMBER=AUTO`, `T0_TEMP=AUTO`, `T1_TEMP=AUTO`.
- `E_SPEED_SCALE=AUTO`, `RETRACT_SPEED_SCALE=AUTO`.
- Smart restore w DUAL layer-clean.
- Poprawione single T0 clean bez dualowego load context.
- Potwierdzone dual T1→T0 clean zgodne z Z-Suite.
- Obsługa profili z dopiskami użytkownika po nazwie kanonicznej.
- Clamp fan `M106 S` do `0..255`.
- Dodany opcjonalny marker `;ZORTRAX_LOAD_FILAMENT`.

## v1.4.16 — nowy marker opcjonalny

```gcode
;ZORTRAX_LOAD_FILAMENT T0
;ZORTRAX_LOAD_FILAMENT T1
;ZORTRAX_LOAD_FILAMENT BOTH
;ZORTRAX_LOAD_FILAMENT AUTO
```

Marker jest domyślnie wyłączony i służy do świadomego wywołania skróconej procedury load-like nad koszem. Nie zastępuje normalnego `TOOLCHANGE_CLEAN`.

## Ostrzeżenia

- Projekt jest reverse engineeringiem formatu classic `.zcode`.
- Testować najpierw krótkie wydruki.
- Nie mieszać plików z różnych wersji.
- Dla single sekcja Tool change / Change filament ma zostać pusta.
- W Filament Advanced dodawać tylko komentarz diagnostyczny `ZORTRAX_FILAMENT_PROFILE`, bez realnych ruchów i temperatur.
