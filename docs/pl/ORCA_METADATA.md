# Powiązanie z metadanymi OrcaSlicer

Konwerter korzysta z trzech źródeł danych:

1. bloku `ORCA METADATA`,
2. standardowych komentarzy Orca,
3. markerów `ZORTRAX_*` w Machine G-code / Change filament G-code.

## Blok `ORCA METADATA`

Konwerter szuka bloku:

```gcode
; ===== ORCA METADATA BEGIN =====
; key=value
; ===== ORCA METADATA END =====
```

Najważniejsze klucze:

| Metadana Orca | Do czego służy w konwerterze |
|---|---|
| `process` | opis/raport źródłowy procesu |
| `filament_t0`, `filament_type_t0` | materiał modelowy T0, mapowany do kodu materiału i nagłówka `62` |
| `filament_t1`, `filament_type_t1` | materiał support/T1, mapowany do kodu materiału i nagłówka `85` |
| `layer_height` | wysokość warstwy, nagłówek `63`; pośrednio jakość `64` |
| `support_threshold_angle` | kąt supportu, nagłówek `66` |
| `infill_density` | wypełnienie, nagłówek `65` |
| `top_layers`, `bottom_layers` | dane diagnostyczne / raportowe |
| `support` | czy support jest aktywny; wpływa na single/dual i triplet `58..60` |
| `support_type` | typ supportu do raportu i decyzji pomocniczych |
| `travel_speed` | prędkość przejazdów; konwerter przelicza mm/s na mm/min |
| `retraction_speed_t0`, `retraction_speed_t1` | prędkości retrakcji narzędzi; używane przy `IDLE_RETRACT=AUTO` |
| `deretraction_speed_t0`, `deretraction_speed_t1` | prędkości deretrakcji/purge; używane przy `PURGE=AUTO` i `START_PURGE` |
| `nozzle_temperature_initial_layer_t0`, `nozzle_temperature_initial_layer_t1` | temperatura narzędzi przed purge startowym |
| `nozzle_temperature_t0`, `nozzle_temperature_t1` | fallback temperatury narzędzi |
| `curr_bed_type` | wybór typu płyty dla temperatur stołu |
| `bed_temp_*_initial`, `bed_temp_*` | temperatura stołu zależna od typu płyty |

## Komentarze fallback

Jeżeli brakuje pełnego bloku `ORCA METADATA`, konwerter wykorzystuje także komentarze:

| Komentarz | Znaczenie |
|---|---|
| `; estimated printing time = ...` | czas wydruku, nagłówek `54..57` |
| `; filament used [mm] = model,support` | długości filamentu, nagłówki `73..74` i `77..78` |
| `; filament_type = ...` | fallback materiału model/support |
| `; filament_settings_id = ...` | fallback materiału model/support z nazwy presetu |
| `; layer_height = ...` | fallback wysokości warstwy |
| `; sparse_infill_density = ...` | fallback infill |
| `; support_threshold_angle = ...` | fallback kąta supportu |
| `; travel_speed = ...` | fallback feedrate przejazdu |
| `; retraction_speed = ...` | fallback prędkości retrakcji |
| `; deretraction_speed = ...` | fallback prędkości deretrakcji |

## `ZORTRAX_TOOLCHANGE_META`

Ten marker przenosi placeholdery Orca z Change filament G-code do konwertera.

Pola najważniejsze dla `ZORTRAX_SPECIAL_CLEAN`:

| Pole | Rola |
|---|---|
| `previous_extruder` | narzędzie opuszczane |
| `next_extruder` | narzędzie aktywowane |
| `layer_num` | numer warstwy, używany przy czyszczeniu co N warstw |
| `flush_length` | długość purge wyliczona przez Orca |
| `old_retract`, `new_retract` | długości retrakcji / deretrakcji |
| `old_e_f`, `new_e_f` | feedrate ekstrudera z Orca |
| `x_after_toolchange`, `y_after_toolchange`, `z_after_toolchange` | pozycja powrotu po zmianie narzędzia |

## Single vs dual

Konwerter traktuje plik jako single, jeżeli:

- długość supportu wynosi `0`, albo
- support jest pusty/równy modelowi i nie ma realnego zużycia drugiego materiału.

Wtedy:

- kod supportu w nagłówku jest ustawiany na kod modelu,
- długość supportu jest `0`,
- triplet `58..60` ma postać `01 02 01`.

Dla realnego dual:

- T0 jest materiałem modelu,
- T1 jest supportem / drugim materiałem,
- triplet `58..60` zależy od materiału supportu:
  - Z-SUPPORT / Plus / Premium: `01 03 00`,
  - BASF BVOH i pozostałe: `01 02 01`.

## Zmienne środowiskowe wyjścia Orca

Dla tymczasowego pliku `.gcode.pp` konwerter szuka finalnej ścieżki wyjścia w:

- `SLIC3R_PP_OUTPUT_PATH`,
- `ORCA_OUTPUT_PATH`,
- `SLIC3R_PP_OUTPUT`,
- `ORCA_OUTPUT`,
- `SLIC3R_PP_OUTPUT_NAME`,
- `ORCA_OUTPUT_NAME`.

Jeżeli Orca nie przekaże finalnej ścieżki dla `.gcode.pp`, konwerter kończy pracę błędem zamiast zapisywać wynik do starego katalogu `out`.
