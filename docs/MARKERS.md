# Markery `ZORTRAX_*`

Markery są komentarzami G-code, które Orca zostawia w pliku, a konwerter zamienia na natywne sekwencje classic ZCode dla Inventure.

## `;ZORTRAX_START_MACHINE`

Składnia:

```gcode
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_MACHINE SINGLE
;ZORTRAX_START_MACHINE DUAL
```

Znaczenie:

- emituje sekwencję startową podobną do Z-Suite,
- wykonuje homing X/Y i Z,
- ustawia pozycje specjalne/drop zone,
- wybiera logikę single/dual.

Najbezpieczniejszy wariant w presetach:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

## `;ZORTRAX_START_PURGE`

Składnia v1.01:

```gcode
;ZORTRAX_START_PURGE AUTO LENGTH=30
;ZORTRAX_START_PURGE SINGLE LENGTH=20
;ZORTRAX_START_PURGE DUAL LENGTH=30
;ZORTRAX_START_PURGE T0 LENGTH=20
;ZORTRAX_START_PURGE T1 LENGTH=20
```

Opcje:

| Opcja | Znaczenie |
|---|---|
| `AUTO` | single: T0, dual: T0+T1 |
| `SINGLE`, `T0`, `MODEL` | purge tylko T0 |
| `T1`, `SUPPORT` | purge tylko T1 |
| `DUAL`, `FULL_DUAL` | purge T0 i T1 |
| `LENGTH=<mm>` | długość fizycznego purge filamentu |
| `PURGE=<mm>` | alias dla `LENGTH=<mm>` |
| `PURGE_F=<feedrate>` / `F=<feedrate>` | wymusza feedrate purge w mm/min |
| `RETRACT=<mm>` | w v1.01 jest parsowane, ale ignorowane w `START_PURGE` |
| `RETRACT_F=<feedrate>` | parsowane, ale nieużywane przy braku retrakcji |

Ważne dla v1.01: `START_PURGE` wykonuje **tylko purge** z `LENGTH`. Nie wykonuje retrakcji po purge. Przed purge aktywny ekstruder jest nagrzewany do temperatury materiału z metadanych Orca (`nozzle_temperature_initial_layer_tN`, fallback `nozzle_temperature_tN`).

## `;ZORTRAX_TOOLCHANGE_META`

Marker pomocniczy wstawiany w Change filament / Toolchange G-code. Nie generuje samodzielnie ruchu, ale zapisuje dane dla następnego czyszczenia/toolchange.

Typowy wariant:

```gcode
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
```

Najważniejsze pola:

- `previous_extruder`, `next_extruder` — narzędzie stare i nowe,
- `layer_num`, `layer_z` — warstwa zmiany,
- `flush_length` — długość purge wyliczona przez Orca,
- `old_retract`, `new_retract`, `old_e_f`, `new_e_f` — retrakcje i prędkości,
- `x_after_toolchange`, `y_after_toolchange`, `z_after_toolchange` — pozycja powrotu.

## `;ZORTRAX_SPECIAL_CLEAN`

Składnia:

```gcode
;ZORTRAX_SPECIAL_CLEAN AUTO
;ZORTRAX_SPECIAL_CLEAN AUTO 5 PURGE=AUTO IDLE_RETRACT=AUTO
;ZORTRAX_SPECIAL_CLEAN DUAL EVERY=5 PURGE
;ZORTRAX_SPECIAL_CLEAN T0 PURGE=8
;ZORTRAX_SPECIAL_CLEAN T1 PURGE=8 IDLE_RETRACT=3
```

Opcje:

| Opcja | Znaczenie |
|---|---|
| `AUTO` | czyści narzędzie wynikające ze stanu/current tool |
| `SINGLE` | sekwencja single |
| `DUAL` / `FULL_DUAL` | pełna sekwencja obu głowic |
| `T0`, `MODEL`, `TOOL0` | czyszczenie T0 |
| `T1`, `SUPPORT`, `TOOL1` | czyszczenie T1 |
| liczba, np. `5` | czyść co N warstw |
| `EVERY=5` / `INTERVAL=5` | równoważny zapis interwału |
| `PURGE` | purge domyślnie 8 mm |
| `PURGE=<mm>` | purge określonej długości |
| `PURGE=AUTO` | użycie długości wynikającej z metadanych/toolchange, jeśli dostępna |
| `PURGE_F=<feedrate>` | feedrate purge |
| `IDLE_RETRACT` | domyślna retrakcja idle 3 mm |
| `IDLE_RETRACT=<mm>` | retrakcja narzędzia przechodzącego w idle |
| `IDLE_RETRACT=AUTO` | użycie retrakcji z metadanych Orca |
| `IDLE_RETRACT_F=<feedrate>` | feedrate retrakcji idle |

## `;ZORTRAX_SPECIAL_POS`

Składnia:

```gcode
;ZORTRAX_SPECIAL_POS MODEL_GARBAGE_OUTSIDE
;ZORTRAX_SPECIAL_POS 0x09
```

Obsługiwane pozycje/aliasy:

| Kod | Nazwa skrócona |
|---|---|
| `0x00` | `GARBAGE_CENTER` |
| `0x01` | `MODEL_SLOW`, `T0_SLOW` |
| `0x02` | `SUPPORT_SLOW`, `T1_SLOW` |
| `0x03` | `MODEL_FAST`, `T0_FAST` |
| `0x04` | `SUPPORT_FAST`, `T1_FAST` |
| `0x05` | `MODEL_BRUSH_AVOID`, `T0_BRUSH_AVOID` |
| `0x06` | `SUPPORT_BRUSH_AVOID`, `T1_BRUSH_AVOID` |
| `0x07` | `MODEL_GARBAGE_SIDE`, `T0_GARBAGE_SIDE` |
| `0x08` | `SUPPORT_GARBAGE_SIDE`, `T1_GARBAGE_SIDE` |
| `0x09` | `MODEL_GARBAGE_OUTSIDE`, `T0_GARBAGE_OUTSIDE` |
| `0x0A` | `SUPPORT_GARBAGE_OUTSIDE`, `T1_GARBAGE_OUTSIDE` |
| `0x0B` | `HOTEND_CLEANING_POSITION`, `HOTEND_CLEAN` |

## `;ZORTRAX_END_MACHINE`

Składnia:

```gcode
;ZORTRAX_END_MACHINE AUTO
;ZORTRAX_END_MACHINE SINGLE
;ZORTRAX_END_MACHINE DUAL
```

Znaczenie:

- emituje sekwencję zakończenia wydruku podobną do Z-Suite,
- dobiera wariant single/dual automatycznie albo jawnie z opcji.
