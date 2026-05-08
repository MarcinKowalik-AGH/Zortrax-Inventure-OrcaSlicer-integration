# Zortrax Inventure / Orca v1.4.1

Wersja: **v1.4.1-production-LAB38-LAB42B-zsuite-t0-clean**  
Status: pełna wersja produkcyjna złożona z potwierdzonych artefaktów LAB, bez przepisywania logiki z opisu.

## Najważniejsze zasady tej wersji

- **Single LAB38 pozostaje nienaruszalny.** To jest potwierdzony dobry stan i nie wolno go zmieniać bez wyraźnego sygnału użytkownika.
- **Dual LAB42B jest potwierdzonym fixem open-file** dla testu cone dual Z-PLA + Z-SUPPORT, raft 50, support=false.
- Nie używać ścieżek odrzuconych: LAB39 fast/minimal, LAB40/LAB41 błędne próby open-file, LAB43_DIRECT.
- Nie rekonstruować kodu z opisów. Źródłem prawdy są pliki `converter/*.py` i referencyjne `.zcode` w `tests/`.

## Instalacja w Orca

Skopiuj zawartość katalogu `converter/` do katalogu skryptów, np.:

Windows:

```text
C:\OrcaScripts\
```

macOS:

```text
/Users/<user>/OrcaScripts/
```

W Orca jako post-processing script ustaw pełną ścieżkę do launchera:

Windows:

```text
C:\OrcaScripts\run_g2z_orca_postprocess.bat
```

macOS:

```text
/Users/<user>/OrcaScripts/run_g2z_orca_postprocess.command
```

## Pliki krytyczne

```text
converter/g2z_wrapper_orca.py
converter/g2z_wrapper_orca_base_lab14_known_good.py
converter/run_g2z_orca_postprocess.bat
converter/run_g2z_orca_postprocess.sh
converter/run_g2z_orca_postprocess.command
```

`g2z_wrapper_orca_base_lab14_known_good.py` musi być obok `g2z_wrapper_orca.py`.

## Potwierdzone referencje

Single LAB38:

```text
tests/single_lab38/zcode/CONE_SUPPORT__V38_01_REFERENCE_CONFIRMED.zcode
tests/single_lab38/zcode/CONE_SUPPORT__V38_01_REGENERATED_BY_RESTORED_CONVERTER.zcode
```

Te dwa pliki są bajtowo identyczne według raportu `reports/LAB38_REPRODUCE_1TO1_report.json`.

Dual LAB42B:

```text
tests/dual_lab42b/zcode/cone_dual_ZPLA_ZSUPPORT_raft50_LAB42B_CONFIRMED.zcode
```

To jest potwierdzony plik open-file dla dual.

## Szybki self-check single LAB38

```bash
python3 tools/reproduce_lab38_single.py
```

Oczekiwany wynik: `byte-for-byte equal: True`.

## Sprawdzenie statystyk `.zcode`

```bash
python3 tools/zcode_stats.py tests/single_lab38/zcode/CONE_SUPPORT__V38_01_REFERENCE_CONFIRMED.zcode
python3 tools/zcode_stats.py tests/dual_lab42b/zcode/cone_dual_ZPLA_ZSUPPORT_raft50_LAB42B_CONFIRMED.zcode
```

## Machine G-code w Orca

Minimalna zasada: używać markerów `ZORTRAX_*`, a nie ręcznie rekonstruować start/czyszczenie.

Single start:

```gcode
;ZORTRAX_START_MACHINE SINGLE E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5
```

Single layer change:

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

Dual start:

```gcode
;ZORTRAX_START_MACHINE DUAL E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5
```

Dual toolchange:

```gcode
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400
```

Dual layer change:

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

End:

```gcode
;ZORTRAX_END_MACHINE AUTO
```


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
