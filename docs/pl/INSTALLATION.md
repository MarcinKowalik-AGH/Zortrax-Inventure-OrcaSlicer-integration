# Instalacja i konfiguracja OrcaSlicer

## 1. Skopiowanie skryptów

Utwórz katalog `OrcaScripts` w katalogu domowym użytkownika i skopiuj do niego zawartość katalogu `scripts/`.

Windows:

```text
C:\Users\<użytkownik>\OrcaScripts\
```

macOS:

```text
/Users/<użytkownik>/OrcaScripts/
```

Na macOS nadaj prawa wykonywania:

```bash
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.sh
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.command
```

## 2. Import presetów Orca

W OrcaSlicer zaimportuj jeden albo oba pliki z `presets/`:

- `Zortrax Inventure 0.4 nozzle - single.orca_printer`
- `Zortrax Inventure 0.4 nozzle - dual.orca_printer`

## 3. Post-processing script

W Orca ustaw pełną ścieżkę do launchera. Nie wpisuj samych zmiennych typu `%USERPROFILE%` lub `$HOME` w polu Orca, bo parser Orca może ich nie rozwinąć tak jak powłoka systemowa.

Windows:

```text
C:\Users\<użytkownik>\OrcaScripts\run_g2z_orca_postprocess.bat
```

macOS:

```text
/Users/<użytkownik>/OrcaScripts/run_g2z_orca_postprocess.command
```

## 4. Machine G-code

Presety `.orca_printer` mają już wstawione właściwe markery.

Dla single:

```gcode
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE SINGLE LENGTH=20
```

Dla dual:

```gcode
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE DUAL LENGTH=30
```

End G-code:

```gcode
;ZORTRAX_END_MACHINE AUTO
```

Toolchange / Change filament dla dual:

```gcode
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_SPECIAL_CLEAN AUTO 5 PURGE=AUTO IDLE_RETRACT=AUTO
M400
```

## 5. Zapis wyniku

Przy wywołaniu przez Orca plik wejściowy ma zwykle postać tymczasowego `.gcode.pp`. Dla takiego pliku konwerter wymaga, aby Orca przekazała finalną ścieżkę Save/Save As w zmiennych środowiskowych, np. `SLIC3R_PP_OUTPUT_NAME`.

Przy ręcznym uruchomieniu z terminala można użyć:

```bash
python3 scripts/g2z_wrapper_orca.py -i model.gcode -o model.zcode --log
```
