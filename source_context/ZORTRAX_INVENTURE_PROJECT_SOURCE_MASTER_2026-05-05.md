# Zortrax Inventure / OrcaSlicer — skonsolidowane źródło projektu

Data konsolidacji: 2026-05-05  
Status: plik nadrzędny do wgrania jako źródło projektu / wiedza dla nowych chatów.

> Ten dokument ma zastąpić rozproszone podsumowania jako główne źródło robocze. Starsze pliki transferowe i raporty są dołączone niżej w appendiksach jako materiał dowodowy i archiwalny.

---

## 1. Aktualny stan roboczy

Projekt dotyczy integracji **Zortrax Inventure** z **OrcaSlicer** i konwertera **G-code → classic `.zcode`** w pure Python. Normalny workflow nie używa Z-Suite ani `g2z.jar` w runtime.

Aktualne linie:

- Produkcyjna: `v1.4.x`, obecnie po hotfixie `v1.4.15_layer_clean_dual_smart_restore`.
- Równoległa patchowa: `v1.2.20`.
- Aktualne presety: `v1.4.14_current_converter`, przygotowane pod konwerter `v1.4.14+`; po poprawce końcowego przełączenia na support aktualny konwerter bazowy do dalszej pracy to `v1.4.15`.

Przy instalacji konwertera zawsze podmieniać oba pliki:

```text
 g2z_wrapper_orca.py
 g2z_wrapper_orca_base_lab14_known_good.py
```

Sama podmiana wrappera nie wystarcza, ponieważ mechaniczna konwersja idzie przez plik bazowy.

---

## 2. Potwierdzone pola nagłówka classic `.zcode` Inventure

Najważniejsze potwierdzone offsety:

```text
54..57  czas druku
58..60  triplet trybu
61      printer id = 0x0A
62      materiał modelu
63      layer
64      quality
65      infill
66      support angle
68..71  software / Z-Suite
73..74  długość filamentu modelowego
77..78  długość filamentu supportowego
85      materiał supportu
127     CRC
```

Triplet:

```text
single i BASF/BVOH  -> 01 02 01
Z-SUPPORT family    -> 01 03 00
```

CRC jest potwierdzone. `byte72` nie jest prostą flagą single/dual; obecna ścieżka open-file/semantics może dawać `0`.

---

## 3. Materiały i kody `.zcode`

### Native / Zortrax

```text
Z-ABS legacy        0x00
Z-ULTRAT            0x01
Z-GLASS             0x02
Z-HIPS              0x03
Z-PCABS             0x04
Z-PETG              0x05
Z-ULTRAT Plus       0x06
Z-SUPPORT           0x07
Z-ESD               0x08
Z-PHA               0x09
Z-PLA               0x0A
Z-PLA Pro           0x0B
Z-ASA Pro           0x0C
Z-SUPPORT Plus      0x0D
Z-SEMIFLEX          0x0E
Z-FLEX              0x0F
Z-NYLON             0x10
Z-SUPPORT Premium   0x11
Z-PEEK              0x12
Z-SUPPORT ATP       0x13 eksperymentalne, potwierdzone tylko z `.zcodex2` M300 Dual, nie dla Inventure classic/RFID
```

External classic: potwierdzone `PETG-based filament = 0x83` w próbce `b1`. BASF Ultrafuse BVOH w classic `.zcode` = `0x17`. Pozostałe external traktować ostrożnie według aktualnej bazy konwertera i próbek.

---

## 4. Polityka nazw presetów

Aktualna polityka: `CANONICAL_PREFIX_PLUS_USER_SUFFIX_ALLOWED`.

Konwerter akceptuje dopiski po nazwie kanonicznej dla filament/process/printer, np.:

```text
Z-PLA test
Z-SUPPORT ATP test
0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual test
Zortrax Inventure 0.4 nozzle - single copy
```

Nie uznawać automatycznie dopisku przed nazwą, np. `Test Z-PLA`.

Najpewniejsze mapowanie filamentów daje komentarz w Advanced:

```gcode
;ZORTRAX_FILAMENT_PROFILE canonical=Z-PLA zcode=0x0A role=model support_role=0 experimental=0
```

W Advanced nie dodawać realnych `M104/M109/G1/T0/T1`, tylko komentarze diagnostyczne dla konwertera.

---

## 5. Polityka temperatur i chamber

Aktualna zasada: **ORCA values override Z-Suite defaults**.

Priorytet:

```text
1. jawna wartość w markerze: CHAMBER=, T0_TEMP=, T1_TEMP=
2. aktualna wartość z Orca metadata / G-code
3. Z-Suite DB / mapa konwertera
4. fallback
```

`AUTO` oznacza ten mechanizm. Inventure nie ma grzanego stołu; w presetach Orca `bed/plate temp` jest nośnikiem temperatury komory (`chamber=bed`).

Konwerter powinien ignorować pre-startowe `M104/M109/M140/M141/M190/M191`, jeśli później występuje `;ZORTRAX_START_MACHINE`, aby automatyczny preheat Orca nie walczył ze startem Zortrax.

---

## 6. Aktualne zalecane Machine G-code

### DUAL start

```gcode
;ZORTRAX_START_MACHINE DUAL CHAMBER=AUTO T0_TEMP=AUTO T1_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO
```

### DUAL toolchange

```gcode
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} direction_model_support={previous_extruder}->{next_extruder} zsuite_direction=AUTO layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400
```

### DUAL layer

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN DUAL EVERY=20 START_LAYER=10 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
;ZORTRAX_LAYER_META layer_num={layer_num} layer_z={layer_z}
```

### SINGLE start

```gcode
;ZORTRAX_START_MACHINE SINGLE CHAMBER=AUTO T0_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO
```

### SINGLE layer

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
;ZORTRAX_LAYER_META layer_num={layer_num} layer_z={layer_z}
```

SINGLE toolchange/change filament: zostawić puste.

---

## 7. `E_SPEED_SCALE`, `RETRACT_SPEED_SCALE`, M83

`E_SPEED_SCALE` i `RETRACT_SPEED_SCALE` dotyczą tylko procedur technicznych generowanych przez konwerter:

```text
START_MACHINE
START_PURGE
TOOLCHANGE_CLEAN
LAYER_CLEAN
```

Nie zmieniają normalnych prędkości druku z process. Skalują feedrate `F`, nie długości E.

AUTO:

```text
support / BVOH / PVA / support family  zwykle 0.6
FLEX / SEMIFLEX                         zwykle 0.8
zwykłe modelowe                         1.0
```

Normalna retrakcja filamentu pochodzi z Orca filament settings / G-code i nie jest tym samym co `IDLE_RETRACT=AUTO` przy toolchange. `IDLE_RETRACT=AUTO` = Z-Suite-like `-20 mm @ F480` z możliwym skalowaniem prędkości.

`Use relative E distances` / `M83`: konwerter wykrywa M83 i robi roboczo Orca-like M82, zachowując fizyczne dystanse E oraz potrzebne `G92 E0`. Nie zmienia długości ekstruzji/retrakcji, tylko sposób zapisu.

---

## 8. Procedury czyszczenia

### Single T0 clean

Potwierdzone w `v1.4.2+`:

```text
FE -> FE -> T0 brush path -> FD -> RESTORE E0
```

Bez `area F4`, bez `DWELL`, bez `SELECT T0`, bez dualowego toolchange/load context.

### Dual T1→T0 clean

Potwierdzone:

```text
E -20 area F3
RESTORE E0
SELECT T0
POS 00
F480 area F4 E21
F2000 area FE E22
DWELL 3000
T0 clean path 0A→08→09→07→0A→08→00
F2000 area FD E21
RESTORE E0
```

T1 clean path:

```text
09→07→0A→08→09→07→00
```

T0 clean path:

```text
0A→08→09→07→0A→08→00
```

### DUAL layer clean smart restore

Po `v1.4.15` `ZORTRAX_LAYER_CLEAN DUAL`:

```text
- czyści aktualny tool,
- czyści drugi tylko jeśli będzie jeszcze użyty później,
- na końcu przywraca pierwotnie aktywny tool.
```

Tryby `FULL_DUAL` / `BOTH` mogą wymusić stare czyszczenie obu.

---

## 9. Prędkości normalnego druku / OP02

Normalne prędkości druku są z:

```text
Process -> G-code F -> OP02 w .zcode
```

Nie z `E_SPEED_SCALE`.

Semantyka OP02/Z-Suite v2:

```text
0x00  model outer
0x02  model inner
0x03  internal solid
0x11  top
0x13  sparse infill
0x04/0x05/0x18  support-speed-controlled
0x1B/0x21       support interface/surface-like; skaluje się global print speed, nie Support Print speed
0x1D/0x1E       printed tower; zwykle F2000 / 33 mm/s
0xFC            travel; F7200 / 120 mm/s
```

`M106 S` musi być clampowane do `0..255`, bo Orca może wygenerować skrajne wartości.

---

## 10. Filament DB i wartości potwierdzone

Presety Orca mają `chamber=bed`, `ZORTRAX_FILAMENT_PROFILE` w Advanced oraz wypełnione sekcje Filament/Cooling/Settings override/Advanced/Multimaterial/Dependencies tam, gdzie możliwe.

Nie da się w samym filament profile zaemulować:

```text
firmware start / basket / homing
bin purge-clean nad pojemnikiem
toolchange clean
single T0 clean
pełnej krzywej Fan Auto
akceleracji per-feature
prawdziwej komory jako sprzętu niezależnego od bed/plate
```

Potwierdzone temperatury / retrakcje single:

```text
Z-ABS 0x00       T0 275  chamber 80  retr 0.8@F2200
Z-ULTRAT         T0 260  chamber 80  retr 1.0@F4400
Z-GLASS          T0 225  chamber 60  retr 2.0@F4800
Z-PETG           T0 225  chamber 60  retr 2.0@F4800
Z-ULTRAT Plus    T0 260  chamber 80  retr 1.0@F4400
Z-ESD            T0 270  chamber 60  retr ok.1.8@F4800
Z-PLA            T0 210  chamber 30  retr 1.0@F2000
Z-PLA Pro        T0 207  chamber 30  retr 1.5@F2100
Z-ASA Pro        T0 260  chamber 80  retr 1.0@F4400
Z-FLEX           T0 230  chamber 40  retr 2.5@F2100
Z-NYLON          T0 250  chamber 80  retr 2.0@F4800
```

Dual z supportem:

```text
Z-PLA / Z-PLA Pro chamber 40
Z-SEMIFLEX chamber 50
Z-GLASS / Z-PETG / Z-ESD chamber 60
Z-ULTRAT Plus chamber 80
T1 support Z-SUPPORT Premium / BVOH 220
T0 examples: PLA 210, GLASS/PETG 235, ULTRAT Plus 260, ESD 270, SEMIFLEX 225
```

PETG-based classic `.zcode` w próbce `b1`: `0x83`, T0 235, chamber 60, Z-SUPPORT Premium `0x11`, T1 220, normal retr 2.0@F4800.

Z-SUPPORT ATP z `.zcodex2`: id `0x13`, support temp 250, normal support retract 2.0@F3600, toolchange retract -20@F480; eksperymentalne dla Inventure.

---

## 11. Brim / raft

Dla `raft_layers > 0` obecny mapping jest poprawny: nie oczekujemy osobnego `area 0x22`; brim/base idzie w semantykę raft/base + jump/connector.

Dla `raft_layers = 0` i realnego `TYPE:Brim` na pierwszej warstwie docelowo trzeba mapować do `area 0x22`. `TYPE:Skirt` testować osobno. Odkładamy do automatycznych testów Z-Suite.

---

## 12. Static Z-Suite readout

Starsze Z-Suite potwierdziło klasy/pojęcia:

```text
CmdLayer, CmdPause, CmdMoveToSpecialPosition, CmdSetFeedrate,
CmdSetExtruderTemperature, FanCommandsMoverInventure, PreviewMesh,
ModelContour/Entrance/Exit, Visible/Invisible/Top/Bottom/BridgeInfill,
SupportInfill/Interface, Raft/RaftBottom/RaftInterface,
WasteTowerModel/Support, Seam, Jump,
ES_RetractionBeforeChangeToModel/Support,
ES_PurgeAfterChangeToModel/Support,
ES_BrushingTimes,
ES_WasteTower*
```

Nie zmieniać ruchów tylko na podstawie stringów. Do zmian potrzebne są natywne `.zcode` i testy fizyczne.

---

## 13. Rekomendacja dla przyszłych chatów

1. Ten plik traktować jako główny kontekst.
2. Szczegóły testów i dowody są w appendiksach niżej.
3. Przy pracy z kodem/presetami zawsze sprawdzać najnowszą paczkę `v1.4.15` i presety `v1.4.14_current_converter` lub ich nowsze odpowiedniki.
4. W razie pytań szczegółowych przeszukiwać ten plik i dołączone raporty, a nie odtwarzać z pamięci.

---

# APPENDIKSY — treść plików transferowych i raportów


## A0. Indeks plików tekstowych scalonych w tym dokumencie

1. `a_settings_inspection/README_a_settings_inspection.md` (6361 B)
2. `a_settings_single_inspection/README_single_native_zsuite_inspection.md` (12047 B)
3. `b1_settings.txt` (953 B)
4. `b3_settings.txt` (954 B)
5. `bunnydecor x1_1extruder_settings.txt` (268 B)
6. `cone_test_temp_material_override_audit_v1412.md` (2327 B)
7. `op02_zsuite_native_feedrate_analysis_2026-05-04/README_OP02_FEEDRATE_ANALYSIS.md` (2975 B)
8. `podsumowanie_zortrax_inventure_rfid_orca.md` (18064 B)
9. `real_orca_v1410_feature_audit/README_real_orca_v1410_feature_audit.md` (6976 B)
10. `w_settings.txt` (330 B)
11. `y_settings.txt` (267 B)
12. `z_settings.txt` (269 B)
13. `zcodex2_material_inspection/README_zcodex2_inspection.md` (1141 B)
14. `zcodex2_material_inspection/zcodex2_material_settings_and_decoded_commands.csv` (1941 B)
15. `ZORTRAX_INVENTURE_calosciowe_ustalenia_i_logika_chatu.md` (20409 B)
16. `ZORTRAX_INVENTURE_chat_logic_i_ustalenia.md` (10689 B)
17. `ZORTRAX_INVENTURE_deep_thread_summary_2026-04-17.md` (17313 B)
18. `Zortrax_Inventure_full_transfer_summary_v1.2.7_2026-04-29.md` (42659 B)
19. `ZORTRAX_INVENTURE_kontekst_transfer_full.md` (15725 B)
20. `Zortrax_Inventure_material_filament_db_v1.4.9.json` (27064 B)
21. `Zortrax_Inventure_Orca_presets_v1.4.14_current_converter_report.md` (4246 B)
22. `Zortrax_Inventure_Orca_presets_v1.4.6_report.md` (2994 B)
23. `Zortrax_Inventure_Orca_presets_v1.4.8_OP02_speed_scaling_report.md` (1520 B)
24. `Zortrax_Inventure_Orca_presets_v1.4.9_filament_db_report.md` (3393 B)
25. `ZORTRAX_INVENTURE_podsumowanie_chatu_homing_kalibracja_2026-04-27.md` (12051 B)
26. `Zortrax_Inventure_Project_Summary.md` (3597 B)
27. `ZORTRAX_INVENTURE_transfer_2026-04-15.md` (13990 B)
28. `ZORTRAX_INVENTURE_transfer_summary_2026-04-15.md` (14133 B)
29. `ZORTRAX_INVENTURE_transfer_summary_2026-04-16.md` (14964 B)
30. `Zortrax_Inventure_transfer_v3.md` (1344 B)
31. `Zortrax_Inventure_v146_temperature_speed_audit.md` (7709 B)
32. `Zortrax_Inventure_v148_process_speed_targets.csv` (539 B)
33. `Zortrax_Inventure_v148_Z_filament_inventory_gaps.csv` (6271 B)
34. `Zortrax_Inventure_v148_Z_filament_inventory_gaps.md` (6165 B)
35. `Zortrax_Inventure_v149_filament_profile_db.csv` (8019 B)
36. `ZSUITE_dependencies_for_converter_report.md` (8108 B)
37. `ZSUITE_OLD_STATIC_READOUT_REPORT.md` (7497 B)

---


## A1. `a_settings_inspection/README_a_settings_inspection.md`

# Inspekcja `a_settings.zip` — Z-Suite native `.zcode` dla Inventure

Zakres paczki: 16 par `*.zcode + *_settings.txt`, próbki `a..p`.

## Najważniejsze ustalenia

1. `Z-SUPPORT Premium` w headerze `.zcode` ma kod `0x11` i triplet `01 03 00`.
2. `BASF Ultrafuse BVOH` w headerze `.zcode` ma kod `0x17` i triplet `01 02 01`.
3. Wszystkie próbki mają `byte72 = 5`, czyli są klasą dual Z-Suite.
4. `OP0E` i `OP16` nadal zachowują się jak temperatura komory — wartości 40/50/60/80 zależnie od materiału.
5. `OP08` potwierdza temperatury narzędzi: T1 support zwykle 220°C, T0 zależnie od materiału.
6. Normalne retrakcje są materiałowo różne i są oddzielne od toolchange/idle retract `-20 mm @ F480`.

## Header / temperatury / retrakcje

| sample | material | support | model | support_code | triplet | chamber | T0 | T1 | retract_main |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a | Z-GLASS | Z-SUPPORT Premium | 0x02 | 0x11 | 01 03 00 | 60 | 235 | 220 | area 0xFD -2.000mm F4800 (94x) |
| b | Z-PETG | Z-SUPPORT Premium | 0x05 | 0x11 | 01 03 00 | 60 | 235 | 220 | area 0xFD -2.000mm F4800 (94x) |
| c | Z-PLA | Z-SUPPORT Premium | 0x0A | 0x11 | 01 03 00 | 40 | 210 | 220 | area 0xFD -1.000mm F2000 (94x) |
| d | Z-ULTRAT Plus | Z-SUPPORT Premium | 0x06 | 0x11 | 01 03 00 | 80 | 260 | 220 | area 0xFD -1.000mm F2000 (94x) |
| e | Z-ESD | Z-SUPPORT Premium | 0x08 | 0x11 | 01 03 00 | 60 | 270 | 220 | area 0xFD -2.000mm F4800 (94x) |
| f | Z-PLA Pro | Z-SUPPORT Premium | 0x0B | 0x11 | 01 03 00 | 40 | 210 | 220 | area 0xFD -1.000mm F2000 (94x) |
| g | Z-PLA Pro | Z-SUPPORT Premium | 0x0B | 0x11 | 01 03 00 | 40 | 210 | 220 | area 0xFD -1.000mm F2000 (94x) |
| h | Z-SEMIFLEX | Z-SUPPORT Premium | 0x0E | 0x11 | 01 03 00 | 50 | 225 | 220 | area 0xFD -2.000mm F2500 (94x) |
| i | Z-SEMIFLEX | BASF Ultrafuse BVOH | 0x0E | 0x17 | 01 02 01 | 50 | 225 | 220 | area 0xFD -2.000mm F2500 (94x) |
| j | Z-PLA Pro | BASF Ultrafuse BVOH | 0x0B | 0x17 | 01 02 01 | 40 | 210 | 220 | area 0xFD -1.000mm F2000 (94x) |
| k | Z-ESD | BASF Ultrafuse BVOH | 0x08 | 0x17 | 01 02 01 | 60 | 270 | 220 | area 0xFD -2.000mm F4800 (94x) |
| l | Z-ULTRAT Plus | BASF Ultrafuse BVOH | 0x06 | 0x17 | 01 02 01 | 80 | 260 | 220 | area 0xFD -1.000mm F2000 (94x) |
| m | Z-PLA | BASF Ultrafuse BVOH | 0x0A | 0x17 | 01 02 01 | 40 | 210 | 220 | area 0xFD -1.000mm F2000 (94x) |
| n | Z-PLA | BASF Ultrafuse BVOH | 0x0A | 0x17 | 01 02 01 | 40 | 210 | 220 | area 0xFD -1.000mm F2000 (94x) |
| o | Z-PETG | BASF Ultrafuse BVOH | 0x05 | 0x17 | 01 02 01 | 60 | 235 | 220 | area 0xFD -2.000mm F4800 (94x) |
| p | Z-GLASS | BASF Ultrafuse BVOH | 0x02 | 0x17 | 01 02 01 | 60 | 235 | 220 | area 0xFD -2.000mm F4800 (94x) |

## Profile prędkości OP02 — skrót

Format komórek: `F mm/min / mm/s`.

| material | support | outer | inner | infill_candidates | sparse | support_speed | interface_0x1B | travel |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Z-ESD | Z-SUPPORT Premium | 1200 / 20.0 | 3500 / 58.3 | 5761 / 96.0 | 6500 / 108.3 | 3000 / 50.0 | 1620 / 27.0 | 7200 / 120.0 |
| Z-ESD | BASF Ultrafuse BVOH | 1200 / 20.0 | 3500 / 58.3 | 5761 / 96.0 | 6500 / 108.3 | 3000 / 50.0 | 1620 / 27.0 | 7200 / 120.0 |
| Z-GLASS | Z-SUPPORT Premium | 1200 / 20.0 | 3500 / 58.3 | 5635 / 93.9 | 6500 / 108.3 | 3500 / 58.3 | 1584 / 26.4 | 7200 / 120.0 |
| Z-GLASS | BASF Ultrafuse BVOH | 1200 / 20.0 | 3500 / 58.3 | 5635 / 93.9 | 6500 / 108.3 | 3500 / 58.3 | 1584 / 26.4 | 7200 / 120.0 |
| Z-PETG | Z-SUPPORT Premium | 1200 / 20.0 | 3500 / 58.3 | 5635 / 93.9 | 6500 / 108.3 | 3500 / 58.3 | 1584 / 26.4 | 7200 / 120.0 |
| Z-PETG | BASF Ultrafuse BVOH | 1200 / 20.0 | 3500 / 58.3 | 5635 / 93.9 | 6500 / 108.3 | 3500 / 58.3 | 1584 / 26.4 | 7200 / 120.0 |
| Z-PLA | Z-SUPPORT Premium | 1200 / 20.0 | 3500 / 58.3 | 6400 / 106.7 | 6500 / 108.3 | 3500 / 58.3 | 2100 / 35.0 | 7200 / 120.0 |
| Z-PLA | BASF Ultrafuse BVOH | 1200 / 20.0 | 3500 / 58.3 | 6400 / 106.7 | 6500 / 108.3 | 3500 / 58.3 | 2100 / 35.0 | 7200 / 120.0 |
| Z-PLA Pro | Z-SUPPORT Premium | 1200 / 20.0 | 3500 / 58.3 | 6400 / 106.7 | 6500 / 108.3 | 3500 / 58.3 | 2100 / 35.0 | 7200 / 120.0 |
| Z-PLA Pro | BASF Ultrafuse BVOH | 1200 / 20.0 | 3500 / 58.3 | 6400 / 106.7 | 6500 / 108.3 | 3500 / 58.3 | 2100 / 35.0 | 7200 / 120.0 |
| Z-SEMIFLEX | Z-SUPPORT Premium | 1200 / 20.0 | 1200 / 20.0 | 2000 / 33.3 | 2000 / 33.3 | 1200 / 20.0 | 2100 / 35.0 | 7200 / 120.0 |
| Z-SEMIFLEX | BASF Ultrafuse BVOH | 1200 / 20.0 | 1200 / 20.0 | 2000 / 33.3 | 2000 / 33.3 | 1200 / 20.0 | 2100 / 35.0 | 7200 / 120.0 |
| Z-ULTRAT Plus | Z-SUPPORT Premium | 1200 / 20.0 | 3500 / 58.3 | 5690 / 94.8 | 6500 / 108.3 | 3500 / 58.3 | 1600 / 26.7 | 7200 / 120.0 |
| Z-ULTRAT Plus | BASF Ultrafuse BVOH | 1200 / 20.0 | 3500 / 58.3 | 5690 / 94.8 | 6500 / 108.3 | 3500 / 58.3 | 1600 / 26.7 | 7200 / 120.0 |

## Interpretacja retrakcji materiałowej

Najczęstsza mała ujemna retrakcja `area 0xFD`:

- Z-GLASS / Z-PETG / Z-ESD: ok. `-2.0 mm @ F4800` = 80 mm/s.
- Z-PLA / Z-PLA Pro / Z-ULTRAT Plus: ok. `-1.0 mm @ F2000` = 33.3 mm/s.
- Z-SEMIFLEX: ok. `-2.0 mm @ F2500` = 41.7 mm/s.

W tych samych plikach występują też większe retrakcje procedur technicznych:
- `area 0xF3` / `0xE9`, około `-20 mm @ F480` — to toolchange/idle retract, nie zwykła retrakcja druku.
- `area 0xFD -2.5 mm @ F3600` lub podobne — występuje w kontekście support/toolchange, nie należy mieszać bezpośrednio z normalną retrakcją filamentu modelowego.

## Implikacje dla Orca

- `Z-SUPPORT Premium` jako support ma być dalej mapowany na `0x11`, a `BASF Ultrafuse BVOH` na `0x17`.
- Triplet musi zależeć od supportu:
  - `Z-SUPPORT Premium` -> `01 03 00`
  - `BASF Ultrafuse BVOH` -> `01 02 01`
- Temperatury komory z tych próbek należy traktować jako potwierdzone dla tych par:
  - Z-PLA / Z-PLA Pro: 40°C
  - Z-SEMIFLEX: 50°C
  - Z-GLASS / Z-PETG / Z-ESD: 60°C
  - Z-ULTRAT Plus: 80°C
- Support T1 w tych próbkach jest 220°C zarówno dla Z-SUPPORT Premium, jak i BASF BVOH.
- Prędkości OP02 mają silną zależność od materiału; nie powinno się stosować jednego globalnego procesu dla wszystkich materiałów, jeśli celem jest bliskość Z-Suite.

## Pliki tabelaryczne

- `a_settings_overview_header_temps_retraction.csv`
- `a_settings_OP02_area_feedrates.csv`
- `a_settings_material_speed_profile_summary.csv`


## A2. `a_settings_single_inspection/README_single_native_zsuite_inspection.md`

# Zortrax Inventure — inspekcja natywnych próbek SINGLE Z-Suite (`a_settings (2).zip`)

Zakres: 13 plików `.zcode` + `*_settings.txt` z Z-Suite 2.32.0.0, tryb single-material.

## Najważniejsze wnioski

1. Wszystkie próbki są single-material:
   - `triplet 58..60 = 01 02 01`
   - `byte72 = 7`
   - `support_len = 0`
   - `support_code = model_code`

2. Potwierdzony został natywny `Z-ABS` jako legacy/native:
   - `Z-ABS = 0x00`
   - `chamber OP0E/OP16 = 80`
   - `T0 = 275°C`
   - normalna retrakcja ok. `0.8 mm @ F2200` (`36.7 mm/s`)

3. Dla single Z-Suite temperatury różnią się od części wcześniejszych dualowych próbek:
   - `Z-PLA` i `Z-PLA Pro` mają tu komorę `30°C`
   - wcześniejsze dualowe próbki z supportem miały dla PLA/PLA Pro wyższą komorę (`40°C`)
   - dlatego baza filamentów powinna rozróżniać co najmniej `single/native` vs `dual/support job`, albo przyjąć konserwatywny override zależny od trybu.

4. Normalna retrakcja materiałowa jest zależna od materiału i nie powinna być mieszana z toolchange/idle retract `-20 mm @ F480`.

## Header / temperatura / retrakcja — próbki

| sample   | material      | model_code_hex   | support_code_hex   | triplet   |   byte72 |   chamber_op0e |   nozzle_t0_max |   normal_retract_mm |   normal_retract_F |   normal_retract_mm_s |   model_len_mm |   support_len_mm |
|:---------|:--------------|:-----------------|:-------------------|:----------|---------:|---------------:|----------------:|--------------------:|-------------------:|----------------------:|---------------:|-----------------:|
| a        | Z-GLASS       | 0x02             | 0x02               | 01 02 01  |        7 |             60 |             225 |               2     |               4800 |                 80    |           1970 |                0 |
| b        | Z-ABS         | 0x00             | 0x00               | 01 02 01  |        7 |             80 |             275 |               0.8   |               2200 |                 36.67 |           2188 |                0 |
| c        | Z-PETG        | 0x05             | 0x05               | 01 02 01  |        7 |             60 |             225 |               2     |               4800 |                 80    |           1970 |                0 |
| d        | Z-ULTRAT      | 0x01             | 0x01               | 01 02 01  |        7 |             80 |             260 |               1     |               4400 |                 73.33 |           2152 |                0 |
| e        | Z-ESD         | 0x08             | 0x08               | 01 02 01  |        7 |             60 |             270 |               1.799 |               4800 |                 80    |           2184 |                0 |
| f        | Z-ESD         | 0x08             | 0x08               | 01 02 01  |        7 |             60 |             270 |               1.799 |               4800 |                 80    |           2184 |                0 |
| g        | Z-ULTRAT Plus | 0x06             | 0x06               | 01 02 01  |        7 |             80 |             260 |               1     |               4400 |                 73.33 |           2185 |                0 |
| h        | Z-PLA Pro     | 0x0B             | 0x0B               | 01 02 01  |        7 |             30 |             207 |               1.5   |               2100 |                 35    |           2148 |                0 |
| i        | Z-ASA Pro     | 0x0C             | 0x0C               | 01 02 01  |        7 |             80 |             260 |               1     |               4400 |                 73.33 |           2028 |                0 |
| j        | Z-ASA Pro     | 0x0C             | 0x0C               | 01 02 01  |        7 |             80 |             260 |               1     |               4400 |                 73.33 |           2028 |                0 |
| k        | Z-FLEX        | 0x0F             | 0x0F               | 01 02 01  |        7 |             40 |             230 |               2.5   |               2100 |                 35    |           2148 |                0 |
| l        | Z-NYLON       | 0x10             | 0x10               | 01 02 01  |        7 |             80 |             250 |               2     |               4800 |                 80    |           2182 |                0 |
| n        | Z-PLA         | 0x0A             | 0x0A               | 01 02 01  |        7 |             30 |             210 |               1     |               2000 |                 33.33 |           1955 |                0 |

## Agregat materiałowy

| material      | model_code_hex   |   chamber_op0e |   nozzle_t0_max |   normal_retract_mm |   normal_retract_F |   normal_retract_mm_s | sample   |
|:--------------|:-----------------|---------------:|----------------:|--------------------:|-------------------:|----------------------:|:---------|
| Z-ABS         | 0x00             |             80 |             275 |               0.8   |               2200 |                 36.67 | b        |
| Z-ULTRAT      | 0x01             |             80 |             260 |               1     |               4400 |                 73.33 | d        |
| Z-GLASS       | 0x02             |             60 |             225 |               2     |               4800 |                 80    | a        |
| Z-PETG        | 0x05             |             60 |             225 |               2     |               4800 |                 80    | c        |
| Z-ULTRAT Plus | 0x06             |             80 |             260 |               1     |               4400 |                 73.33 | g        |
| Z-ESD         | 0x08             |             60 |             270 |               1.799 |               4800 |                 80    | e,f      |
| Z-PLA         | 0x0A             |             30 |             210 |               1     |               2000 |                 33.33 | n        |
| Z-PLA Pro     | 0x0B             |             30 |             207 |               1.5   |               2100 |                 35    | h        |
| Z-ASA Pro     | 0x0C             |             80 |             260 |               1     |               4400 |                 73.33 | i,j      |
| Z-FLEX        | 0x0F             |             40 |             230 |               2.5   |               2100 |                 35    | k        |
| Z-NYLON       | 0x10             |             80 |             250 |               2     |               4800 |                 80    | l        |

## OP02 / feedrate — zaokrąglone prędkości dla single

Wartości w tabeli są `F / 60`, zaokrąglone do całych `mm/s`.

| sample   | material      |   outer_wall_speed |   inner_wall_speed |   internal_solid_infill_speed |   sparse_infill_speed |   top_surface_speed |   support_speed |   support_interface_speed |   travel_speed |   raft_first_layer_speed |   raft_base_speed |
|:---------|:--------------|-------------------:|-------------------:|------------------------------:|----------------------:|--------------------:|----------------:|--------------------------:|---------------:|-------------------------:|------------------:|
| a        | Z-GLASS       |                 25 |                 30 |                            33 |                    40 |                  25 |              40 |                        30 |            120 |                       10 |                47 |
| b        | Z-ABS         |                 20 |                 45 |                            48 |                    60 |                  40 |              40 |                        47 |            120 |                       10 |                50 |
| c        | Z-PETG        |                 25 |                 30 |                            33 |                    40 |                  25 |              40 |                        30 |            120 |                       10 |                47 |
| d        | Z-ULTRAT      |                 25 |                 25 |                            50 |                    40 |                  40 |              40 |                        30 |            120 |                       10 |                50 |
| e        | Z-ESD         |                 17 |                 25 |                            50 |                    40 |                  40 |              40 |                        40 |            120 |                       10 |                50 |
| f        | Z-ESD         |                 17 |                 25 |                            50 |                    40 |                  40 |              40 |                        40 |            120 |                       10 |                50 |
| g        | Z-ULTRAT Plus |                 16 |                 25 |                            40 |                    40 |                  40 |              40 |                        30 |            120 |                       15 |                50 |
| h        | Z-PLA Pro     |                 20 |                 25 |                            37 |                    40 |                  40 |              40 |                        29 |            120 |                       10 |                50 |
| i        | Z-ASA Pro     |                 20 |                 25 |                            80 |                    60 |                  40 |              40 |                        30 |            120 |                       15 |                50 |
| j        | Z-ASA Pro     |                 20 |                 25 |                            80 |                    60 |                  40 |              40 |                        30 |            120 |                       15 |                50 |
| k        | Z-FLEX        |                 20 |                 25 |                            30 |                    25 |                  40 |              25 |                        30 |            120 |                        5 |                20 |
| l        | Z-NYLON       |                 23 |                 40 |                            47 |                    50 |                  40 |              40 |                        28 |            120 |                       10 |                50 |
| n        | Z-PLA         |                 20 |                 25 |                            40 |                    25 |                  33 |              40 |                        35 |            120 |                       10 |                50 |

## Interpretacja dla presetów Orca

### Filament

Do `filament/*.json` można wykorzystać:

- `filament_retraction_length`
- `filament_retraction_speed`
- `filament_deretraction_speed` jako bazę równą lub bliską retraction speed,
- `nozzle_temperature`
- `chamber_temperature` oraz plate-temp jako `chamber=bed` dla Inventure.

Najważniejsze potwierdzone wartości single:

| Materiał | T0 | Chamber | Retraction |
|---|---:|---:|---|
| Z-ABS | 275 | 80 | 0.8 mm @ 36.7 mm/s |
| Z-ULTRAT | 260 | 80 | 1.0 mm @ 73.3 mm/s |
| Z-GLASS | 225 | 60 | 2.0 mm @ 80 mm/s |
| Z-PETG | 225 | 60 | 2.0 mm @ 80 mm/s |
| Z-ULTRAT Plus | 260 | 80 | 1.0 mm @ 73.3 mm/s |
| Z-ESD | 270 | 60 | 1.8 mm @ 80 mm/s |
| Z-PLA | 210 | 30 | 1.0 mm @ 33.3 mm/s |
| Z-PLA Pro | 207 | 30 | 1.5 mm @ 35 mm/s |
| Z-ASA Pro | 260 | 80 | 1.0 mm @ 73.3 mm/s |
| Z-FLEX | 230 | 40 | 2.5 mm @ 35 mm/s |
| Z-NYLON | 250 | 80 | 2.0 mm @ 80 mm/s |

### Process speed

OP02 pokazuje, że natywne single ma mocne różnice materiałowe. Jeden process globalny jest kompromisem.
Dla pełnej zgodności można rozważyć procesy materiałowe albo przynajmniej klasy:
- szybkie/twarde: ABS, ASA, ULTRAT, NYLON
- PLA/PETG/GLASS
- FLEX
- ESD

### Ważna ostrożność

Prędkości `0x04/0x05/0x18` występują także w single mimo `support_len=0`, bo w single support/raft/support-like struktury są liczone do materiału modelu. Nie należy z samego `support_len=0` usuwać semantyki tych obszarów z body.


## A3. `b1_settings.txt`

Application version: 2.32.0.0
Estimated print time: 7h 40m
Material usage: 6.31m (19g)
Support usage: 6.36m (14g)
Printer: Zortrax Inventure
Profile: Last settings
Support type: Automatic
Support: 45°
Support material: Z-SUPPORT Premium
Material: PETG-based filament
Nozzle diameter: 0.4 mm
Layer: 0.15 mm
Quality: Default
Infill: 20%
Fan speed: Auto
Seam: Normal
Outer contours: 0.00
Holes: 0.00
Contour-infill gap: 0.34
Contour-top gap: 0.31
Surface layers Top: 7
Surface layers Bottom: 3
Max. wall thickness: 3.13 mm
Print speed: +0%
Extruder flow ratio: +0%
Top layer infill (%): 100
Bottom layer infill (%): 100
Extrusion temp.: 235
Chamber temp.: 60
Retraction speed: 80
Retraction distance: 2.0
Support Density: 5.00 mm
Support temp.: 220
Anti-warping ring: Yes
Support Print speed: 100%
Support Flow ratio: 100%
Hybrid Support: No
Support Surface layers: 4
Support Surface density: 100%
Cooling tower: No


## A4. `b3_settings.txt`

Application version: 2.32.0.0
Estimated print time: 8h 42m
Material usage: 6.31m (19g)
Support usage: 6.36m (14g)
Printer: Zortrax Inventure
Profile: Last settings
Support type: Automatic
Support: 45°
Support material: Z-SUPPORT Premium
Material: PETG-based filament
Nozzle diameter: 0.4 mm
Layer: 0.15 mm
Quality: Default
Infill: 20%
Fan speed: Auto
Seam: Normal
Outer contours: 0.00
Holes: 0.00
Contour-infill gap: 0.34
Contour-top gap: 0.31
Surface layers Top: 7
Surface layers Bottom: 3
Max. wall thickness: 3.13 mm
Print speed: -50%
Extruder flow ratio: +0%
Top layer infill (%): 100
Bottom layer infill (%): 100
Extrusion temp.: 235
Chamber temp.: 60
Retraction speed: 80
Retraction distance: 2.0
Support Density: 5.00 mm
Support temp.: 220
Anti-warping ring: Yes
Support Print speed: 120%
Support Flow ratio: 100%
Hybrid Support: No
Support Surface layers: 4
Support Surface density: 100%
Cooling tower: No


## A5. `bunnydecor x1_1extruder_settings.txt`

Application version: 2.32.0.0
Estimated print time: 6h 16m
Material usage: 19.81m (56g)
Printer: Zortrax Inventure
Profile: Last settings
Support type: Automatic
Support: 30°
Material: Z-PLA
Nozzle diameter: 0.4 mm
Layer: 0.15 mm
Quality: High
Infill: 50%


## A6. `cone_test_temp_material_override_audit_v1412.md`

# Audit — cone_0.3_Z-PLA test + Z-SUPPORT ATP test

## Input G-code values from Orca

The uploaded G-code contains the +1°C edits in the filament presets:

```text
nozzle_temperature_t0 = 211
nozzle_temperature_t1 = 251
nozzle_temperature_initial_layer_t0 = 211
nozzle_temperature_initial_layer_t1 = 251
chamber_temperature_t0 = 31
chamber_temperature_t1 = 91
bed_temp_hot_initial_t0/t1 = 31 / 91
bed_temp_hot_t0/t1 = 31 / 91
```

It also contains explicit start override values in Machine start G-code:

```gcode
;ZORTRAX_START_MACHINE DUAL CHAMBER=45 T0_TEMP=215 T1_TEMP=225 ...
```

Therefore the explicit marker still wins for the start sequence. Toolchange/preheat temperatures still follow Orca's current values, so repeated OP08 temperatures include T0=211 and T1=251.

## Uploaded ZCode problem

The uploaded ZCode has wrong material header values:

```text
model material   = 0x65
support material = 0x01
fw_triplet       = 01 02 01
```

That happened because the visible preset names were renamed with a suffix: `Z-PLA test`, `Z-SUPPORT ATP test`. The older converter did not reliably use `;ZORTRAX_FILAMENT_PROFILE canonical=... zcode=...` as a material-code source.

## Fixed in v1.4.12 / v1.2.17

The hotfix adds two safe fallbacks:

1. Longest-prefix material-name matching, so `Z-PLA test` maps to `Z-PLA`.
2. `;ZORTRAX_FILAMENT_PROFILE` canonical/zcode support for material-code fallback.

After reconversion with v1.4.12:

```text
model material   = 0x0A
support material = 0x13
fw_triplet       = 01 03 00
```

Temperature result with the current G-code is:

```text
OP0E / OP16 chamber = 45   # from explicit START_MACHINE CHAMBER=45
OP08 T0 includes 211       # from Orca filament +1°C during toolchanges
OP08 T1 includes 251       # from Orca support filament +1°C during toolchanges
OP08 T0 also includes 215  # explicit start/standby marker value
OP08 T1 also includes 225  # explicit start marker value
```

## Practical recommendation

For normal modifiable temperatures, do not hard-code `CHAMBER=... T0_TEMP=... T1_TEMP=...` in `ZORTRAX_START_MACHINE`. Use:

```gcode
;ZORTRAX_START_MACHINE DUAL E_SPEED_SCALE=0.4 RETRACT_SPEED_SCALE=1
```

Then the converter can use the current Orca values as the real job values. Keep explicit `CHAMBER=...` only when you intentionally want to override Orca.


## A7. `op02_zsuite_native_feedrate_analysis_2026-05-04/README_OP02_FEEDRATE_ANALYSIS.md`

# OP02 / feedrate analysis — Zortrax Inventure native Z-Suite candidates

Scanned selected project source ZIPs, nested chat upload/source archives, current packages, and top-level `.zcode` files. Found 250 `.zcode` references, 82 unique binaries, 63 native Z-Suite candidates after excluding LAB/test/patched/g2z/generated artifacts.

## Decoder

`OP02` is decoded as `06 02 <feedrate_i32_le> CRC`; value is mm/min, mm/s = F/60. Active OP02 is assigned to following OP01 movement commands by area byte.

## Global dominant speeds from native candidates

| Area | Meaning | F mm/min | mm/s | Moves | Distribution top |
|---|---|---:|---:|---:|---|
| 0x00 | outer_wall_candidate | 1200 | 20.0 | 1063072 | `1200:642997; 600:158384; 1800:34591; 300:11076; 400:7353; 869:7192; 811:3798; 979:3439` |
| 0x02 | inner_wall_candidate | 3500 | 58.33 | 342073 | `3500:194528; 1500:116043; 5250:10398; 1750:10179; 2700:6688; 1200:1536; 1800:1520; 2400:720` |
| 0x03 | internal_solid_infill_candidate | 6400 | 106.67 | 259041 | `6400:142388; 2400:63041; 3000:9083; 2000:6654; 8000:4469; 3200:4404; 2496:2856; 2467:2448` |
| 0x13 | sparse_infill_candidate | 6500 | 108.33 | 337432 | `6500:191092; 1500:100601; 2400:15564; 8000:10050; 3250:9815; 3600:7440; 2000:1678; 3000:787` |
| 0x11 | top_surface_candidate | 4000 | 66.67 | 74857 | `4000:49561; 2000:16543; 2400:4434; 6000:4275; 1500:32; 1656:12` |
| 0x0A | raft_bottom_or_clean_pos_related | 1000 | 16.67 | 9416 | `1000:6014; 600:2742; 900:437; 970:112; 300:111` |
| 0x0C | raft_interface_candidate | 7200 | 120.0 | 10667 | `7200:5427; 3000:4300; 4200:634; 900:184; 6984:122` |
| 0x1D | printed_waste_tower_model_candidate | 2000 | 33.33 | 57446 | `2000:57446` |
| 0x1E | printed_waste_tower_support_candidate | 2000 | 33.33 | 43868 | `2000:43868` |
| 0xFC | travel_candidate | 7200 | 120.0 | 807289 | `7200:789261; 8000:8987; 3600:8484; 4968:494; 2000:27; 4800:17; 2200:9; 4400:5` |
| 0xFB | travel_candidate | 7200 | 120.0 | 3206 | `7200:3206` |

## Files

- `op02_area_feedrate_native_zsuite_candidates.csv`: detailed decoded OP02-by-area table for native candidates.
- `op02_representative_speeds_native_zsuite_candidates.csv`: wide representative speed table per file.
- `op02_global_area_speed_matrix_native_zsuite_candidates.csv`: aggregate by material/support/area.
- `zcode_inventory_unique_all.csv`: all unique `.zcode` binaries and native-candidate classification.
- `existing_prior_speed_databases/`: previous decoded speed databases found in project packages.
- `project_text_search_hits_op02_feedrate_limited.csv`: source/chat summary hits for OP02/feedrate/speed terms.

## Notes

- No native per-feature acceleration table was found; only OP02 feedrate is decoded here.
- Area names are reverse-engineered candidates.
- Bin purge/clean areas such as `0xFE`, `0xFD`, `0xF4`, `0xEA`, `0xE9`, `0xF3` must not be mapped to printed model speeds.
- Printed tower candidates `0x1D/0x1E` remain separate from bin purge/clean.


## A8. `podsumowanie_zortrax_inventure_rfid_orca.md`

# Podsumowanie projektu: Zortrax Inventure, RFID `.mfd`, materiały External i presety Orca

Data opracowania: 2026-04-27  
Zakres: komplet ustaleń z rozmowy do przeniesienia do innego chatu.

---

## 1. Cel projektu

Celem było rozgryzienie i praktyczne wykorzystanie tagów RFID/NFC filamentów Zortrax Inventure zapisanych jako pliki `.mfd`, przygotowanie działających plików RFID dla materiałów Zortrax i External, korekta wag do stanu full / 350 g, oraz modyfikacja presetów i konfiguracji Orca Slicer.

---

## 2. Format `.mfd`

Plik `.mfd` traktujemy jako dump MIFARE Classic 1K:

- 16 sektorów,
- 4 bloki po 16 bajtów na sektor,
- 1024 bajty razem.

Najważniejsze dane materiału są w:

- Sector 1 / block 4,
- Sector 1 / block 5,
- Sector 1 / block 6,
- Sector 2 / block 8,
- Sector 2 / block 10.

---

## 3. Sector 1 / block 4 — identyfikacja materiału

Układ 16 bajtów:

```text
[0]    kod materiału
[1]    wybór głowicy / rodzina materiału
[2]    zwykle 07
[3]    wariant / podrodzina
[4]    kod koloru / selector / profil
[5..7] wartość surowa ilości nominalnej, little-endian
[8..14] flagi / zera / warianty
[15]   CRC8_DVB_S2 z bajtów 0..14
```

Przykład PLA Black:

```text
0A E1 07 06 03 BE C7 01 00 00 00 00 00 00 00 3D
```

Interpretacja:

```text
0A          kod materiału: Z-PLA
E1 07 06    rodzina/głowica: materiał podstawowy
03          kolor/profil: Black
BE C7 01    wartość surowa ilości
3D          CRC8_DVB_S2
```

---

## 4. Sector 1 / block 5 — nazwa koloru lub materiału

Block 5 przechowuje nazwę w ASCII, maksymalnie 16 bajtów.

Zaobserwowane wartości:

| ASCII | HEX |
|---|---|
| Black | `42 6C 61 63 6B` |
| Grey | `47 72 65 79` |
| Ivory | `49 76 6F 72 79` |
| Graphite | `47 72 61 70 68 69 74 65` |
| Natural White | `4E 61 74 75 72 61 6C 20 57 68 69 74 65` |
| RED | `52 45 44` |
| Transparent | `54 72 61 6E 73 70 61 72 65 6E 74` |
| External | `45 78 74 65 72 6E 61 6C` |

Dla materiałów podporowych block 5 zostawiano pusty.

---

## 5. Sector 1 / block 6 — CRC sektora

Block 6 zwykle ma 15 bajtów zer i CRC w ostatnim bajcie.

CRC liczone jest z:

```text
block4 pełne 16 bajtów
+ block5 pełne 16 bajtów
+ block6 pierwsze 15 bajtów
```

Razem 47 bajtów.

---

## 6. Sector 2 / block 8 — aktualna ilość materiału

Układ:

```text
[0..2] aktualna wartość surowa, little-endian
[3..14] zwykle zera
[15] CRC8_DVB_S2 z bajtów 0..14
```

Przykład:

```text
BE C7 01 00 00 00 00 00 00 00 00 00 00 00 00 D7
```

---

## 7. Sector 2 / block 10 — CRC sektora

CRC w ostatnim bajcie block 10 liczone jest z:

```text
block8 pełne 16 bajtów
+ block9 pełne 16 bajtów
+ block10 pierwsze 15 bajtów
```

---

## 8. CRC8_DVB_S2

Parametry praktyczne:

```text
poly = 0xD5
init = 0x00
bez final xor
bez odbicia bitów
```

Funkcja Python:

```python
def crc8_dvb_s2(data: bytes) -> int:
    crc = 0x00
    poly = 0xD5
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc
```

Zasady:

```text
block4[15]  = CRC8_DVB_S2(block4[0:15])
block8[15]  = CRC8_DVB_S2(block8[0:15])
block6[15]  = CRC8_DVB_S2(block4 + block5 + block6[0:15])
block10[15] = CRC8_DVB_S2(block8 + block9 + block10[0:15])
```

---

## 9. Rodziny materiałów / wybór głowicy

W block 4 bajty `[1..3]` są bardzo ważne.

| Rodzina | Bajty `[1..3]` | Przykłady |
|---|---|---|
| podstawowe | `E1 07 06` | PLA, PETG, Glass, PCABS, HIPS, PHA, ASA, Nylon |
| UltraT / wysokotemperaturowe | `E1 07 0C` | UltraT, UltraT Plus, czasem PEEK |
| podporowe | `E2 07 0C` | Z-Support, Z-Support Plus, Z-Support Premium |
| elastyczne | `E2 07 01` | Z-SemiFlex, Z-Flex |

Błędna rodzina powodowała błędne rozpoznawanie materiału.

---

## 10. Kody materiałów Zortrax

| Kod | Materiał |
|---|---|
| `01` | Z-UltraT |
| `02` | Z-Glass |
| `03` | Z-HIPS |
| `04` | Z-PCABS |
| `05` | Z-PETG |
| `06` | Z-UltraT Plus |
| `07` | Z-Support |
| `08` | Z-ESD |
| `09` | Z-PHA |
| `0A` | Z-PLA |
| `0B` | Z-PLA Pro |
| `0C` | Z-ASA Pro |
| `0D` | Z-Support Plus |
| `0E` | Z-SemiFlex |
| `0F` | Z-Flex |
| `10` | Z-Nylon |
| `11` | Z-Support Premium |
| `12` | Z-PEEK |

Ważne korekty:

- `01` to Z-UltraT, nie Z-ABS.
- `12` to Z-PEEK, nie Z-BVOH.
- Z-BVOH nie ma potwierdzonego kodu w tej standardowej mapie; w External pojawił się jako `0x83`.

---

## 11. Kody External

| Kod | Materiał External |
|---|---|
| `80` | External / Generic External |
| `81` | External ABS-based filament |
| `83` | BASF Ultrafuse BVOH |
| `84` | GLASS-type filament |
| `85` | FLEX-based filament |
| `86` | PLA-based filament |
| `87` | PETG-based filament |
| `89` | NYLON-based filament |
| `91` | ULTRAT-based filament |
| `92` | ESD PETG-based filament |
| `94` | PLA Pro-based filament |
| `95` | ASA Pro-based filament |
| `96` | SEMIFLEX-based filament |

Obserwacje:

- `0x13` nie został rozpoznany przez firmware.
- `0x80` powoduje wyświetlenie `External`.
- Na bazie `0x80` generowano też testy `0x78`, `0x79`, `0x81`.

---

## 12. Masa i wartość surowa

Masa nie jest zapisana bezpośrednio jako gramy.

Wyświetlana masa zależy od:

```text
kod materiału + wartość surowa
```

Wartość surowa jest 3-bajtowa, little-endian.

Wzór korekty:

```text
nowa_wartość = stara_wartość * 350 / odczyt_gramów
```

Python:

```python
old = int.from_bytes(raw3, "little")
new = round(old * 350 / measured_grams)
new_raw3 = new.to_bytes(3, "little")
```

Po zmianie raw trzeba zmienić:

- block 4 bajty 5..7,
- block 8 bajty 0..2,
- CRC block 4,
- CRC block 6,
- CRC block 8,
- CRC block 10.

---

## 13. Potwierdzone i ważne kalibracje

### Z-PLA `0A`

Najlepszy jest oryginalny dump PLA Black.

Block 4:

```text
0A E1 07 06 03 BE C7 01 00 00 00 00 00 00 00 3D
```

Block 8:

```text
BE C7 01 00 00 00 00 00 00 00 00 00 00 00 00 D7
```

Wynik: poprawne 350 g.

Wartość `08 C9 01` dawała 351 g, więc została odrzucona dla PLA i wrócono do oryginalnego dumpa.

### Z-PETG `05`

Raw:

```text
55 C4 01
```

Potwierdzone jako ok.

### Z-Glass `02`

Kolor ma być `Transparent`.

Raw po korekcie:

```text
7E C4 01
```

### Z-Support `07`

Raw roboczy:

```text
1E D3 01
```

Potwierdzone jako ok.

### Z-Support Plus `0D`

Raw:

```text
CB FA 01
```

Block 4:

```text
0D E2 07 0C 12 CB FA 01 00 01 00 00 00 00 00 F1
```

Block 8:

```text
CB FA 01 00 00 00 00 00 00 00 00 00 00 00 00 7E
```

Potwierdzone jako ok.

### Z-Support Premium `11`

Raw:

```text
9C 78 02
```

Block 4:

```text
11 E2 07 0C 12 9C 78 02 00 01 00 00 00 00 00 2A
```

Potwierdzone jako ok.

### Z-SemiFlex `0E`

Raw full:

```text
DA E9 01
```

Block 4:

```text
0E E2 07 01 04 DA E9 01 00 00 00 00 00 00 00 FB
```

Block 8:

```text
DA E9 01 00 00 00 00 00 00 00 00 00 00 00 00 13
```

Potwierdzone jako ok.

### Z-Flex `0F`

Początkowo pokazywał 282 g.  
Po korekcie do 350 g raw:

```text
F9 5F 02
```

### Z-ESD `08`

Początkowo 358 g.  
Po korekcie do 350 g raw:

```text
39 BA 01
```

### Z-HIPS `03`

Początkowo 288 g.  
Po korekcie do 350 g raw:

```text
D6 29 02
```

### Z-Nylon `10`

Początkowo 226 g.  
Po korekcie do 350 g raw:

```text
84 BC 02
```

### Z-PEEK `12`

Początkowo 407 g.  
Po korekcie do 350 g raw:

```text
40 A5 01
```

### Z-PHA `09`

Początkowo 349 g.  
Po korekcie do 350 g raw:

```text
08 C9 01
```

### Z-PLA Pro `0B`

Początkowo 373 g.  
Po korekcie do 350 g raw:

```text
A4 AB 01
```

---

## 14. External `0x80`

Kod `0x80` jest rozpoznawany przez firmware Inventure jako External.

Dobry plik External 80 pokazywał najpierw 116 g.  
Po korekcie do 350 g:

Stary raw:

```text
BE C7 01
```

Nowy raw:

```text
16 5F 05
```

Block 4:

```text
80 E1 07 06 03 16 5F 05 00 00 00 00 00 00 00 73
```

Block 8:

```text
16 5F 05 00 00 00 00 00 00 00 00 00 00 00 00 F4
```

Wniosek: External `0x80` ma inny przelicznik gramów niż standardowe Z-PLA.

---

## 15. Finalne nazewnictwo plików `.mfd`

Ustalony schemat:

```text
NazwaMateriału_Kod_Kolor_full.mfd
```

Dla supportów kolor pusty:

```text
Z-Support_07__full.mfd
Z-SupportPlus_0D__full.mfd
Z-SupportPremium_11__full.mfd
```

Dla Z-Glass:

```text
Z-Glass_02_Transparent_full.mfd
```

Dla normalnych materiałów:

```text
Z-PLA_0A_Black_full.mfd
Z-PETG_05_Black_full.mfd
```

---

## 16. Zweryfikowane finalne materiały

Lista zweryfikowanych / końcowo używanych plików:

```text
Z-PLA_0A_Black_full.mfd
Z-PLAPro_0B_Black_full.mfd
Z-ASAPro_0C_Black_full.mfd
Z-PETG_05_Black_full.mfd
Z-PCABS_04_Black_full.mfd
Z-Glass_02_Transparent_full.mfd
Z-UltraT_01_Black_full.mfd
Z-UltraTPlus_06_Black_full.mfd
Z-ESD_08_Black_full.mfd
Z-HIPS_03_Black_full.mfd
Z-PHA_09_Black_full.mfd
Z-Nylon_10_Black_full.mfd
Z-PEEK_12_Black_full.mfd
Z-Flex_0F_Black_full.mfd
Z-SemiFlex_0E_Black_full.mfd
Z-Support_07__full.mfd
Z-SupportPlus_0D__full.mfd
Z-SupportPremium_11__full.mfd
```

---

## 17. Presety Orca External

Z paczki `Filament presets.zip` z presetami `Z-...` wygenerowano presety:

```text
External MATERIAL.json
External MATERIAL @INVENTURE.json
```

Przykłady:

```text
External PLA.json
External PLA @INVENTURE.json
External PETG.json
External Nylon.json
External ASA Pro @INVENTURE.json
External UltraT.json
```

W JSON ustawiano:

```json
"filament_vendor": ["EXTERNAL"],
"from": "User"
```

oraz poprawiano:

```json
"name": "External PLA",
"filament_settings_id": ["External PLA"]
```

Dla wariantów Inventure:

```json
"name": "External PLA @INVENTURE",
"filament_settings_id": ["External PLA @INVENTURE"]
```

---

## 18. `.orca_printer` jako ZIP

Plik `.orca_printer` jest archiwum ZIP.

Wewnątrz są m.in.:

```text
printer/Zortrax Inventure 0.4 nozzle.json
filament/*.json
process/*.json
bundle_structure.json
```

Aby dodać filamenty External do konfiguracji drukarki:

1. dodać JSON-y do `filament/`,
2. ustawić w nich:
   ```json
   "compatible_printers": ["Zortrax Inventure 0.4 nozzle"],
   "compatible_printers_condition": "",
   "from": "User",
   "filament_vendor": ["EXTERNAL"]
   ```
3. dopisać je w `bundle_structure.json` do:
   ```json
   "filament_config": [...]
   ```

---

## 19. Krytyczna pułapka Orca: `inherits`

Podczas podmiany procesu:

```text
0.15mm Quality @Zortrax Inventure 0.4 nozzle
```

na ustawienia z:

```text
0.15mm Quality @Zortrax Inventure 0.4 nozzle -20
```

nie wolno zostawić self-inherits.

Błędnie:

```json
"name": "0.15mm Quality @Zortrax Inventure 0.4 nozzle",
"inherits": "0.15mm Quality @Zortrax Inventure 0.4 nozzle"
```

Poprawnie:

```json
"name": "0.15mm Quality @Zortrax Inventure 0.4 nozzle",
"inherits": "",
"from": "User",
"compatible_printers": ["Zortrax Inventure 0.4 nozzle"],
"compatible_printers_condition": "",
"print_settings_id": "0.15mm Quality @Zortrax Inventure 0.4 nozzle"
```

Profile pochodne mogą dziedziczyć z bazowego:

```json
"inherits": "0.15mm Quality @Zortrax Inventure 0.4 nozzle"
```

Użytkownik potwierdził, że po usunięciu self-inherits było ok. To trzeba pamiętać przy każdej kolejnej modyfikacji.

---

## 20. Procedura poprawnej podmiany procesu 0.15 mm

1. Otworzyć `.orca_printer` jako ZIP.
2. Wczytać:
   ```text
   process/0.15mm Quality @Zortrax Inventure 0.4 nozzle -20.json
   ```
3. Zapisać jego ustawienia jako:
   ```text
   process/0.15mm Quality @Zortrax Inventure 0.4 nozzle.json
   ```
4. Nadpisać pola tożsamości:
   ```json
   "name": "0.15mm Quality @Zortrax Inventure 0.4 nozzle",
   "inherits": "",
   "from": "User",
   "compatible_printers": ["Zortrax Inventure 0.4 nozzle"],
   "compatible_printers_condition": "",
   "print_settings_id": "0.15mm Quality @Zortrax Inventure 0.4 nozzle"
   ```
5. Upewnić się, że plik jest w `bundle_structure.json -> process_config`.
6. Nie tworzyć duplikatu `bundle_structure.json` w ZIP.

---

## 21. Python — bezpieczna podmiana procesu w `.orca_printer`

```python
from pathlib import Path
import zipfile, json

src = Path("Zortrax Inventure 0.4 nozzle.orca_printer")
out = Path("Zortrax Inventure 0.4 nozzle_modified.orca_printer")

target_name = "process/0.15mm Quality @Zortrax Inventure 0.4 nozzle.json"
source_name = "process/0.15mm Quality @Zortrax Inventure 0.4 nozzle -20.json"
target_display = "0.15mm Quality @Zortrax Inventure 0.4 nozzle"
printer_name = "Zortrax Inventure 0.4 nozzle"

with zipfile.ZipFile(src, "r") as zin:
    files = {name: zin.read(name) for name in zin.namelist()}

source_obj = json.loads(files[source_name].decode("utf-8"))

source_obj["name"] = target_display
source_obj["inherits"] = ""
source_obj["from"] = "User"
source_obj["compatible_printers"] = [printer_name]
source_obj["compatible_printers_condition"] = ""
source_obj["print_settings_id"] = target_display

if "setting_id" in source_obj:
    source_obj["setting_id"] = target_display

files[target_name] = json.dumps(
    source_obj,
    indent=4,
    ensure_ascii=False
).encode("utf-8")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
    for name, data in files.items():
        zout.writestr(name, data)
```

---

## 22. Python — korekta masy w `.mfd`

```python
from pathlib import Path

def crc8_dvb_s2(data: bytes) -> int:
    crc = 0x00
    poly = 0xD5
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

def update_amount(data: bytearray, raw3: bytes):
    b4 = 4 * 16
    b8 = 8 * 16

    data[b4+5:b4+8] = raw3
    data[b4+15] = crc8_dvb_s2(bytes(data[b4:b4+15]))

    block4 = bytes(data[b4:b4+16])
    block5 = bytes(data[5*16:6*16])
    block6_15 = bytes(data[6*16:6*16+15])
    data[6*16+15] = crc8_dvb_s2(block4 + block5 + block6_15)

    data[b8:b8+3] = raw3
    data[b8+15] = crc8_dvb_s2(bytes(data[b8:b8+15]))

    block8 = bytes(data[b8:b8+16])
    block9 = bytes(data[9*16:10*16])
    block10_15 = bytes(data[10*16:10*16+15])
    data[10*16+15] = crc8_dvb_s2(block8 + block9 + block10_15)
```

---

## 23. Python — generowanie block 4 / 5 / 8

```python
def make_material_blocks(mat_code, family, raw3, color_name=None):
    if family == "basic":
        hdr = [0xE1, 0x07, 0x06]
        selector = 0x03
        tail = [0x00] * 7
    elif family == "ultrat":
        hdr = [0xE1, 0x07, 0x0C]
        selector = 0x04
        tail = [0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
    elif family == "support":
        hdr = [0xE2, 0x07, 0x0C]
        selector = 0x12
        tail = [0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
        color_name = None
    elif family == "flex":
        hdr = [0xE2, 0x07, 0x01]
        selector = 0x04
        tail = [0x00] * 7
    else:
        raise ValueError(family)

    block4_15 = bytes([mat_code, *hdr, selector, *raw3, *tail])
    block4 = block4_15 + bytes([crc8_dvb_s2(block4_15)])

    if color_name:
        b = color_name.encode("ascii")[:16]
        block5 = b + bytes(16 - len(b))
    else:
        block5 = bytes(16)

    block8_15 = raw3 + bytes(12)
    block8 = block8_15 + bytes([crc8_dvb_s2(block8_15)])

    return block4, block5, block8
```

---

## 24. Zasady na przyszłość

### Korekta masy

Nie przebudowywać pliku od zera, jeśli tag działa. Zmieniać tylko:

```text
Sector 1 / block 4 bajty 5..7
Sector 2 / block 8 bajty 0..2
CRC block 4
CRC block 6
CRC block 8
CRC block 10
```

### Zmiana materiału

Zmienić:

```text
block 4 byte 0 = kod materiału
block 4 bytes 1..3 = rodzina/głowica
block 4 byte 4 = selector
block 5 = kolor/nazwa, jeśli dotyczy
CRC
```

### Zmiana samej nazwy koloru

Zmienić tylko:

```text
block 5
block 6 CRC
```

### Supporty

Dla supportów block 5 zostawiać pusty.

### Orca

Zawsze sprawdzać `inherits`. Proces bazowy nie może dziedziczyć sam z siebie.

---

## 25. Najważniejsze pliki wygenerowane podczas pracy

W rozmowie wygenerowano m.in.:

```text
support_premium_material07_350g_wcopy.mfd
support_plus_material0D_from07_wcopy.mfd
support_plus_350g_corrected_full.mfd
support_plus_350g_from346_recalculated.mfd
z_glass_material02_350g_corrected_from392.mfd
z_flex_material0F_red_template.mfd
z_semiflex_black_full.mfd
zortrax_materials_pack.zip
zortrax_materials_pack_v2.zip
zortrax_corrected_pack.zip
zortrax_good_pack.zip
zortrax_corrected_and_new_pack.zip
zortrax_missing_materials_pack.zip
zortrax_recalibrated_350g.zip
zortrax_verified_materials.zip
zortrax_external_filaments_0x80_0x99.zip
zortrax_external_78_79_81.zip
zortrax_external_named_materials.zip
external_orca_package.zip
orca_external_complete_presets.zip
orca_external_clean_presets.zip
Zortrax Inventure 0.4 nozzle + External CLEAN.orca_printer
Zortrax Inventure 0.4 nozzle + External CLEAN modified v3.orca_printer
Zortrax Inventure 0.4 nozzle_modified_0.15_from_-20.orca_printer
External_80_80_full_350g.mfd
```

---

## 26. Skrót dla następnego chatu

1. `.mfd` to MIFARE Classic 1K.
2. Kod materiału: Sector 1 / block 4 / byte 0.
3. Nominalny raw: block 4 / bytes 5..7.
4. Aktualny raw: Sector 2 / block 8 / bytes 0..2.
5. Raw jest little-endian.
6. CRC: CRC8_DVB_S2, poly `0xD5`.
7. Dla masy zmieniać raw w block 4 i 8 oraz CRC w block 4, 6, 8, 10.
8. `0x80` = External w firmware Inventure.
9. External 0x80 dla 350 g: raw `16 5F 05`.
10. Przy Orca proces bazowy nie może mieć self-`inherits`.
11. Dla procesu bazowego 0.15 mm skopiowanego z `-20` ustawić `inherits` na pusty string.
12. Dla materiałów podporowych block 5 zostawiać pusty.
13. Dla Z-Glass kolor to `Transparent`.
14. Dla zwykłych materiałów używać `Black`.

---

## 27. Status końcowy

Projekt osiągnął działający model:

- RFID Zortrax: rozpoznana struktura, CRC, mapowanie kodów, rodziny głowic.
- Masy: metoda kalibracji i konkretne wartości raw dla wielu materiałów.
- External: kod `0x80` działa jako External; znana korekta do 350 g.
- Orca: presety External i konfiguracja `.orca_printer`; znana pułapka `inherits`.

Ten plik jest kompletną notatką roboczą do kontynuowania pracy w innym czacie.


## A9. `real_orca_v1410_feature_audit/README_real_orca_v1410_feature_audit.md`

# Real Orca / v1.4.10 feature audit

Input G-code: `cone_0.3_Z-PLA_Z-SUPPORT_51m36s.gcode`  
Input Z-code: `cone_0.3_Z-PLA_Z-SUPPORT_51m36s.zcode`

## Reproducibility check

I re-ran the newest available converter package `v1.4.10_fan_clamp_version_fix` on the supplied G-code.

| File | Size | SHA256 |
|---|---:|---|
| uploaded ZCode | 526480 | `eefbdb44fd406b5b1822527f63c80d58195d38ca9fad73fa9af8d332369b7075` |
| reconverted v1.4.10 | 526480 | `eefbdb44fd406b5b1822527f63c80d58195d38ca9fad73fa9af8d332369b7075` |

Byte-for-byte equal: **True**.

## G-code metadata / markers

ORCA METADATA keys: 77  
ZSUITE HINT keys: 30

Important metadata:

```text
mode=DUAL
process=0.30mm Draft @Zortrax Inventure 0.4 nozzle - dual
layer_height=0.3
filament_t0=Z-PLA / type=PLA
filament_t1=Z-SUPPORT / type=PVA
support=true support_angle=45
infill=15
travel_speed=120
support_speed=58
support_interface_speed=40
raft_layers=4
brim_type=auto_brim brim_width=8
chamber_temperature_t0=30
chamber_temperature_t1=60
```

Marker counts:

| Marker | Count |
|---|---:|
| `;ZORTRAX_FILAMENT_PROFILE` | 68 |
| `;ZORTRAX_TOOLCHANGE_META` | 68 |
| `;ZORTRAX_TOOLCHANGE_CLEAN` | 68 |
| `;ZORTRAX_LAYER_CLEAN` | 197 |
| `;ZORTRAX_LAYER_META` | 197 |
| `;ZORTRAX_START_MACHINE` | 1 |
| `;ZORTRAX_END_MACHINE` | 1 |

Toolchange distribution:

| Count | previous -> next | old_temp -> new_temp | old_retract/new_retract | flush_length |
|---:|---|---|---|---:|
| 1 | -1 -> 1 | 0 -> 220 | 0/10 | 0 |
| 34 | 1 -> 0 | 220 -> 210 | 10/10 | 0 |
| 33 | 0 -> 1 | 210 -> 220 | 10/10 | 0 |

## Header decoded from generated .zcode

```json
{
  "command_count_50_53": 38483,
  "print_time_sec_54_57": 3096,
  "triplet_58_60": "01-03-00",
  "printer_id_61": 10,
  "model_material_62": 10,
  "layer_63": 30,
  "quality_64": 2,
  "infill_65": 15,
  "support_angle_66": 45,
  "byte72": 0,
  "model_len_mm_73_74": 1711,
  "support_len_mm_77_78": 1376,
  "support_material_85": 7,
  "crc_127": 175
}
```

Expected material logic:

```text
model 0x0A = Z-PLA
support 0x07 = Z-SUPPORT
triplet 01-03-00 = Z-SUPPORT-family dual job
```

## Command-stream integrity

Parsed commands: 38483  
Header command count: 38483  
Parser errors: []

Opcode counts of selected features:

| Opcode | Count | Meaning |
|---:|---:|---|
| 0x01 | 29819 | axis / extrusion / fan moves |
| 0x02 | 5117 | feedrate OP02 |
| 0x05 | 3 | home |
| 0x07 | 80 | select tool |
| 0x08 | 356 | tool temperature |
| 0x0E | 2 | chamber-like set |
| 0x10 | 199 | layer marker |
| 0x0F | 0 | pause marker |
| 0x11 | 912 | special position / clean path |
| 0x1A | 3 | firmware state marker |
| 0x15 | 1 | firmware transition marker |

## Feature checks

### Fan / M106 clamp

G-code M106 count: 202  
M106 values outside 0..255 in G-code: 1

Out-of-range M106 values found:

```text
line 21424: M106 S2383706846 ; enable fan
```

ZCode B/fan moves: 203  
ZCode B/fan min/max: 0 / 255  
ZCode B/fan values >255: 0

Result: **fan clamp is working** — the raw huge `M106 S...` from Orca did not reach ZCode as an invalid value.

### ZSUITE HINTS and filament profile comments

Converter output reports:

```text
Detected ZSUITE HINT keys: zsuite_bin_clean_enabled, zsuite_bin_clean_t0_path, zsuite_bin_clean_t1_path, zsuite_brim_type, zsuite_brim_width, zsuite_brushing_times, zsuite_chamber_as_bed, zsuite_classic_zcode, zsuite_extruder_switch_in_firmware, zsuite_generator, zsuite_profile_schema, zsuite_purge_after_change_to_model, zsuite_purge_after_change_to_model_speed, zsuite_purge_after_change_to_support, zsuite_purge_after_change_to_support_speed, zsuite_raft_contact_distance, zsuite_raft_expansion, zsuite_raft_first_layer_density, zsuite_raft_first_layer_expansion, zsuite_raft_layers, zsuite_retraction_before_change_to_model, zsuite_retraction_before_change_to_model_speed, zsuite_retraction_before_change_to_support, zsuite_retraction_before_change_to_support_speed, zsuite_sleep_time_before_brushing, zsuite_target_machine, zsuite_waste_tower_enable, zsuite_waste_tower_model_area, zsuite_waste_tower_source, zsuite_waste_tower_support_area
Z-Suite static compatibility audit:
  zsuite_hints=30, filament_profiles=68, policy=LOG_ONLY
```

Detected hints include model/support purge/retract semantics, brushing, bin-clean paths, tower areas and raft/brim values.

### Temperatures / chamber

Chamber-like OP0E/OP16 commands:

```text
OP0E = 60
OP0E = 40
OP16 = 40
```

Tool temperature setpoints observed in OP08 include:

```text
Counter({(0, 210): 110, (1, 220): 109, (1, 224): 34, (1, 216): 34, (0, 214): 33, (0, 206): 33, (0, 90): 1, (0, 0): 1, (1, 0): 1})
```

Note: the stream contains an early `OP0E=60` from Orca preheat/M190 and then `OP0E/OP16=40` from the Z-Suite-like start/profile logic. For Z-PLA + support, 40°C matches the newer dual-job profile; the early 60°C is a config/converter cleanup candidate.

### Toolchange / clean

Tool selects:

```text
{'T1': 40, 'T0': 40}
```

Special positions summary:

```text
{'0x06': 34, '0x09': 154, '0x04': 34, '0x02': 34, '0x00': 160, '0x07': 120, '0x0A': 154, '0x08': 120, '0x05': 34, '0x03': 34, '0x01': 34}
```

Dual-clean audit from converter:

```text
  single_hint=False, area_F4_E_moves=40, dwell_3000=80, status=OK
```

Result: dual clean/toolchange is active. `area_F4` and `DWELL 3000` are present because this is dual; they would be a problem in single, not here.

### Layers / raft / seam / pause

OP10 layer markers: 199  
First layer markers: [-6, 0, 2, 3, 4, 5, 6, 7, 8, 9]  
Last layer markers: [189, 190, 191, 192, 193, 194, 195, 196, 197, 198]

OP0F pause markers: 0

Semantics line from converter:

```text
  semantics={'tower_t1_to_support': 2189, 'raft_print_to_class': 473, 'raft_nonprint_to_jump': 26, 'seam_to_0xDF': 210}
  ;PAUSE_PRINT markers=0, inserted OP0F pauses=0
```

Area counts of selected classes:

| Area | Count | E-moves | Meaning |
|---|---:|---:|---|
| 0xDF | 210 | 9 | seam |
| 0x1D | 2283 | 2074 | tower/model |
| 0x1E | 2189 | 2189 | tower/support |
| 0x04/0x05/0x18 | 1700 | 1620 | support-speed controlled groups |
| 0x1B/0x21 | 0 | 0 | support surface/interface-like groups |

## Items to watch

1. `M106 S2383706846` is present in the Orca G-code. The new fan clamp handles it correctly, but this confirms why the previous converter crashed.
2. Early chamber command is 60°C, then Z-Suite-like start sets 40°C. This should not break conversion, but it may cause unnecessary heating/waiting. The next cleanup should ignore/suppress Orca preamble `M190/M140` when `ZORTRAX_START_MACHINE` is present, or adjust support-role bed/chamber propagation.
3. Header byte72 is `0`. This matches the current converter output exactly; treat it as current open-file policy unless Z-Suite/printer shows a problem.
4. Filament profile comments are diagnostic/audit only. Some support-role comments may say `mode=SINGLE` because the filament preset is not fully mode-aware; converter logic is still driven by job metadata and toolchange markers.


## A10. `w_settings.txt`

Application version: 2.32.0.0
Estimated print time: 1h 20m
Material usage: 1.92m (5g)
Support usage: 1.44m (4g)
Printer: Zortrax M300 Dual
Profile: Last settings
Support type: Automatic
Support: 35°
Support material: Z-SUPPORT ATP
Material: Z-ULTRAT
Nozzle diameter: 0.4 mm
Layer: 0.15 mm
Quality: High
Infill: 50%


## A11. `y_settings.txt`

Application version: 2.32.0.0
Estimated print time: 0h 39m
Material usage: 2.22m (5g)
Printer: Zortrax M200 Plus
Profile: Last settings
Support type: Automatic
Support: 30°
Material: Z-ABS
Nozzle diameter: 0.4 mm
Layer: 0.14 mm
Quality: High
Infill: 50%


## A12. `z_settings.txt`

Application version: 2.32.0.0
Estimated print time: 0h 44m
Material usage: 2.26m (7g)
Printer: Zortrax M200 Plus
Profile: Last settings
Support type: Automatic
Support: 30°
Material: Z-PCABS
Nozzle diameter: 0.4 mm
Layer: 0.14 mm
Quality: High
Infill: 50%


## A13. `zcodex2_material_inspection/README_zcodex2_inspection.md`

# ZCodeX2 inspection – y/z/w samples

Statyczna inspekcja kontenera `.zcodex2` jako ZIP. Pliki zawierają `UserSettingsData` JSON, `AdditionalMetadata` JSON, binarny `ZCodeData` oraz `ConfigurationData`.

Najważniejsze: z `.zcodex2` można odczytać ustawienia materiałów i część komend binarnych, ale nie jest to classic Inventure `.zcode` i nie należy bezpośrednio mieszać headerów.

W `ZCodeData` dla tych drukarek jednostka E wygląda jak 1000 jednostek/mm, więc np. `E -800` = `-0.8 mm`, a nie skala 960 kroków/mm używana w naszych analizach classic Inventure.

## Summary

- `y.zcodex2`: Zortrax M200 Plus, Z-ABS id 0x00, support None , T0 275°C, support 0°C, platform 80°C, retract 0.800000011920929 mm @ 36 mm/s.
- `z.zcodex2`: Zortrax M200 Plus, Z-PCABS id 0x04, support None , T0 290°C, support 0°C, platform 85°C, retract 1.2000000476837158 mm @ 73 mm/s.
- `w.zcodex2`: Zortrax M300 Dual, Z-ULTRAT id 0x01, support Z-SUPPORT ATP 0x13, T0 260°C, support 250°C, platform 90°C, retract 1.0 mm @ 50 mm/s.

CSV files:
- `zcodex2_material_settings_and_decoded_commands.csv`
- `zcodex2_area_feedrate_summary.csv`


## A14. `zcodex2_material_inspection/zcodex2_material_settings_and_decoded_commands.csv`

```csv
file,printer,material,material_id_dec,material_id_hex,support_material,support_material_id_dec,support_material_id_hex,layer,quality,infill,extruder_temp_setting,support_temp_setting,platform_temp_setting,chamber_temp_setting,retraction_speed_setting_mm_s,retraction_distance_setting_mm,OP0E_values,OP16_values,OP08_tool_temps_unique,top_feedrates,negative_E_top_units_1000_per_mm,positive_E_top_units_1000_per_mm,commands_parsed
y.zcodex2,Zortrax M200 Plus,Z-ABS,0,0x00,,,,0.14 mm,High,50%,275,0,80,-1,36,0.800000011920929,80,,T0=0; T0=275,F2200x730; F2400x509; F7200x486; F2100x211; F1800x165; F1200x144; F1500x143; F2700x121; F3000x81; F2738x21; F2789x20; F600x2,area 0xFD E -800 @F2200 x729 (-0.800mm @ 36.7mm/s),area 0xFE E +802 @F2200 x729 (0.802mm @ 36.7mm/s),34425
z.zcodex2,Zortrax M200 Plus,Z-PCABS,4,0x04,,,,0.14 mm,High,50%,290,0,85,-1,73,1.2000000476837158,85,,T0=0; T0=290,F4400x886; F2400x451; F7200x410; F1200x248; F1800x190; F1500x122; F1342x79; F1684x70; F1718x68; F1092x53; F2105x35; F2148x34,area 0xFD E -1200 @F4400 x885 (-1.200mm @ 73.3mm/s),area 0xFE E +1202 @F4400 x885 (1.202mm @ 73.3mm/s),35958
w.zcodex2,Zortrax M300 Dual,Z-ULTRAT,1,0x01,Z-SUPPORT ATP,19,0x13,0.15 mm,High,50%,260,250,90,-1,50,1.0,90,,T0=0; T0=90; T0=217; T0=222; T0=236; T0=238; T0=260; T1=0; T1=180; T1=191; T1=196; T1=198; T1=200; T1=202; T1=250,F3000x797; F3600x471; F7200x446; F2000x359; F2400x190; F480x161; F1200x136; F1500x126; F500x82; F5000x80; F4922x22; F4862x22,area 0xFD E -1000 @F3000 x93 (-1.000mm @ 50.0mm/s); area 0xFD E -2000 @F3600 x41 (-2.000mm @ 60.0mm/s); area 0xF3 E -20000 @F480 x41 (-20.000mm @ 8.0mm/s); area 0xE9 E -20000 @F480 x40 (-20.000mm @ 8.0mm/s),area 0xFE E +1000 @F3000 x651 (1.000mm @ 50.0mm/s); area 0xFE E +2019 @F3600 x312 (2.019mm @ 60.0mm/s); area 0xFD E +5111 @F3000 x81 (5.111mm @ 50.0mm/s); area 0xFD E +4912 @F3600 x80 (4.912mm @ 60.0mm/s); area 0xFD E +1701 @F3000 x77 (1.701mm @ 50.0mm/s),50137

```


## A15. `ZORTRAX_INVENTURE_calosciowe_ustalenia_i_logika_chatu.md`

# ZORTRAX INVENTURE — całościowe ustalenia, logika, powiązania i wyniki prac

Ten plik zbiera **cały roboczy stan projektu** z rozmów dotyczących:
- drukarki **Zortrax Inventure**,
- presetów **Orca Slicer**,
- konwersji **G-code -> Z-code** przez `g2z.jar`,
- patchowania nagłówka `.zcode`,
- logiki materiałów i supportów,
- workflow **Windows** i **macOS Sequoia**,
- diagnozy błędów post-processingu w Orca.

Plik ma służyć jako **pełny transfer kontekstu do nowego chatu** bez odtwarzania ustaleń od zera.

---

## 1. Główny cel projektu

Celem projektu jest uzyskanie stabilnego workflow:

**Orca Slicer -> G-code -> g2z.jar -> patcher -> poprawny `.zcode` dla Zortrax Inventure**

oraz równolegle:
- przygotowanie poprawnych presetów Orca dla Inventure,
- rozdzielenie i uporządkowanie trybów `single` / `dual`,
- poprawne mapowanie materiałów Zortrax i external,
- zgodność plików wynikowych z zachowaniem Z-Suite i drukarki.

---

## 2. Najważniejszy aktualny stan projektu

Na obecnym etapie są cztery główne obszary pracy:

1. **Patcher `.zcode` dla Inventure**
   - aktywna linia robocza wywodzi się z `g2z_hybrid_wrapper_v10_orca_outdir_named.py`
   - wrapper czyta metadane z G-code z Orca i patchuje potwierdzone pola nagłówka classic `.zcode`
   - logika CRC jest uznana za potwierdzoną

2. **Presety i bundle Orca**
   - docelowo preferowany jest **jeden bundle** z:
     - 2 drukarkami: `single` i `dual`
     - 4 procesami `single`
     - 4 procesami `dual`
     - wspólnymi filamentami

3. **Mapowanie materiałów i supportów**
   - ustalono mapowanie materiałów Zortrax i external
   - ustalono logikę supportów i znaczenie krytycznych bajtów nagłówka

4. **Workflow macOS Sequoia**
   - wersja windowsowa działała, ale na macOS pojawił się problem z post-processingiem w Orca
   - główna przyczyna została rozpoznana: aplikacja GUI Orca uruchamia skrypt z bardzo ubogim `PATH`
   - konieczne jest **jawne wykrywanie prawdziwej Javy**, nie poleganie na samym `java` ani na stubie `/usr/bin/java`

---

## 3. Potwierdzone pola nagłówka classic `.zcode` dla Inventure

To są pola uznane za potwierdzone roboczo dla classic ZCode Inventure:

- `54..57` — czas druku
- `61` — printer id
- `62` — materiał modelowy
- `63` — layer
- `64` — quality
- `65` — infill
- `66` — support angle / parametr supportu używany przez Z-Suite
- `68..71` — wersja Z-Suite / software version
- `73..74` — długość filamentu modelowego
- `77..78` — długość filamentu supportowego
- `85` — materiał supportowy
- `127` — CRC nagłówka

Dodatkowo praktycznie potwierdzono znaczenie bajtów:
- `58..60` — triplet trybu kompatybilności / trybu zadania / profilu firmware

---

## 4. Krytyczne ustalenie o bajtach 58–60

Ostateczne ustalenie:
- **58–60 nie są kodami materiałów**
- są traktowane jako **triplet trybu zadania / kompatybilności / profilu firmware**
- w praktyce decydują o rozpoznaniu typu supportu przez Inventure

Potwierdzona logika:

- **single-material** -> `01 02 01`
- **dual + BASF Ultrafuse BVOH** -> `01 02 01`
- **dual + Z-SUPPORT** -> `01 03 00`
- **dual + Z-SUPPORT Plus** -> `01 03 00`
- **dual + Z-SUPPORT Premium** -> `01 03 00`

Wniosek praktyczny:
- rodzina **Z-SUPPORT / Plus / Premium** używa trybu `01 03 00`
- **BASF BVOH** i wydruk single używają `01 02 01`

---

## 5. Potwierdzone mapowanie materiałów

### 5.1. Natywne materiały Zortrax

- `Z-ULTRAT` -> `0x01`
- `Z-GLASS` -> `0x02`
- `Z-HIPS` -> `0x03`
- `Z-PCABS` -> `0x04`
- `Z-PETG` -> `0x05`
- `Z-ULTRAT PLUS` -> `0x06`
- `Z-SUPPORT` -> `0x07`
- `Z-ESD` -> `0x08`
- `Z-PHA` -> `0x09`
- `Z-PLA` -> `0x0A`
- `Z-PLA PRO` -> `0x0B`
- `Z-ASA PRO` -> `0x0C`
- `Z-SUPPORT PLUS` -> `0x0D`
- `Z-SEMIFLEX` -> `0x0E`
- `Z-FLEX` -> `0x0F`
- `Z-NYLON` -> `0x10`
- `Z-SUPPORT PREMIUM` -> `0x11`
- `Z-PEEK` -> `0x12`

### 5.2. Materiały external / open

- `ABS-BASED FILAMENT` -> `0x81`
- `GLASS-TYPE FILAMENT` -> `0x84`
- `FLEX-BASED FILAMENT` -> `0x85`
- `PLA-BASED FILAMENT` -> `0x86`
- `PETG-BASED FILAMENT` -> `0x87`
- `NYLON-BASED FILAMENT` -> `0x89`
- `ULTRAT-BASED FILAMENT` -> `0x91`
- `ESD PETG-BASED FILAMENT` -> `0x92`
- `PLA PRO-BASED FILAMENT` -> `0x94`
- `ASA PRO-BASED FILAMENT` -> `0x95`
- `SEMIFLEX-BASED FILAMENT` -> `0x96`

### 5.3. BASF support

Najważniejsze robocze ustalenie:
- `BASF ULTRAFUSE BVOH` -> **`0x17`**

To należy traktować jako aktywną, poprawną logikę roboczą patchera dla Inventure.
Aliasy typu:
- `BVOH`
- `ULTRAFUSE BVOH`
- `BASF BVOH`

powinny mapować do `0x17`.

---

## 6. Ustalenie o CRC

To jest uznane za potwierdzone:

- algorytm CRC używany w patcherze jest poprawny
- CRC w bajcie `127` jest liczone prawidłowo
- CRC zgadza się z referencyjnymi plikami `.zcode` z Z-Suite

Wniosek:
- jeśli drukarka zgłasza błąd materiału, **nie wygląda to na problem CRC**, tylko raczej na niezgodność jednego z pól nagłówka, najczęściej:
  - `62`
  - `85`
  - `58..60`
  - ewentualnie powiązania materiałów model/support

---

## 7. Aktywna logika patchera `.zcode`

Docelowa logika patchera dla Inventure:

1. czyta G-code z Orca
2. odczytuje blok `ORCA METADATA`
3. wyciąga z niego m.in.:
   - `process`
   - `layer_height`
   - `filament_t0`
   - `filament_t1`
   - `support`
   - `support_type`
   - `support_threshold_angle`
   - `infill_density`
   - `top_layers`
   - `bottom_layers`
4. czyta fallbacki z komentarzy typu:
   - `; estimated printing time = ...`
   - `; filament used [mm] = ...`
   - `; filament_type = ...`
   - `; filament_settings_id = ...`
   - `; layer_height = ...`
5. ustala:
   - `model_code`
   - `support_code`
   - `single_material`
   - `support_length_mm`
   - `model_length_mm`
   - `quality`
6. uruchamia `g2z.jar`
7. patchuje nagłówek `.zcode`
8. przelicza CRC

### Reguła single-material

Plik należy traktować jako single, jeśli:
- `support_length_mm == 0`
- albo support code jest pusty / równy modelowi i nie ma realnego zużycia supportu

W single:
- `support_code` powinien zostać ustawiony na `model_code`
- `support_length_mm = 0`
- `58..60 = 01 02 01`

### Reguła fw_triplet

Aktywna logika:
- jeśli support realnie występuje i `support_code` należy do rodziny Z-SUPPORT (`0x07`, `0x0D`, `0x11`) -> `01 03 00`
- we wszystkich pozostałych przypadkach -> `01 02 01`

---

## 8. Wyniki testów patchera

### 8.1. Single

Potwierdzone działanie dla single:
- `58–60 = 01 02 01`
- `85 = model_code`
- CRC poprawne

### 8.2. Dual + BASF BVOH

Potwierdzone działanie:
- `58–60 = 01 02 01`
- `62 = model material`
- `85 = 0x17`

### 8.3. Dual + Z-SUPPORT family

Potwierdzone działanie:
- `Z-SUPPORT` -> `85 = 0x07`, `58–60 = 01 03 00`
- `Z-SUPPORT Plus` -> `85 = 0x0D`, `58–60 = 01 03 00`
- `Z-SUPPORT Premium` -> `85 = 0x11`, `58–60 = 01 03 00`

### 8.4. Workflow 1-stopniowy i 2-stopniowy

Były testowane dwa workflow:

#### A. 1-stopniowy
`gcode -> g2z.jar -> patcher`

Wniosek:
- działa poprawnie dla testów `single`, `dual + BASF`, `dual + Z-SUPPORT family`

#### B. 2-stopniowy
1. `java -jar g2z.jar ...`
2. `python patcher.py --no-run-jar ...`

Wniosek:
- również działa poprawnie i jest dobrym workflow diagnostycznym

---

## 9. Bardzo ważne zastrzeżenie metodologiczne

Był moment, kiedy wyciągnięto zły wniosek z porównania **nieekwiwalentnych plików**:
- patched `.zcode` z Orca dla jednego modelu
- oryginalny `.zcode` z Z-Suite dla innego modelu / innych ustawień

Ten wniosek należy uznać za **odrzucony**.

Nie wolno bez ścisłego porównania zakładać, że problem powoduje np.:
- `66`
- `support_threshold_angle`
- albo inne pole nagłówka,

jeśli porównywane pliki nie dotyczą:
- tego samego modelu,
- możliwie tego samego profilu,
- podobnych ustawień materiału i supportu.

Poprawna metoda porównania:
- ten sam model
- możliwie ten sam profil
- Orca G-code
- wynik `g2z.jar`
- wynik `g2z.jar + patch`
- referencyjny `.zcode` z Z-Suite

---

## 10. Ustalenia dotyczące `.orca_printer` i bundli Orca

### 10.1. Docelowa organizacja

Preferowany finalny wariant:
- **1 bundle `.orca_printer`**
- **2 presety drukarki**:
  - `Zortrax Inventure 0.4 nozzle - single`
  - `Zortrax Inventure 0.4 nozzle - dual`
- **8 processów**:
  - 4 dla `single`
  - 4 dla `dual`
- **wspólne filamenty**

### 10.2. Reguły spójności bundla

Przy każdej zmianie pilnować:
- poprawności ZIP
- poprawności JSON
- zgodności z `bundle_structure.json`
- braku osieroconych referencji
- spójności pól:
  - `name`
  - `printer_settings_id`
  - `print_settings_id`
  - `filament_settings_id`
  - nazwy pliku JSON
  - wpisów w `bundle_structure.json`
  - `compatible_printers`

### 10.3. Zmiany nazw presetów

Przy zmianie nazwy presetu trzeba zmieniać jednocześnie:
- `name`
- odpowiednie `*_settings_id`
- nazwę pliku presetowego
- wpisy w `bundle_structure.json`
- referencje w `compatible_printers`

### 10.4. Scalanie presetów

Przy scalaniu presetów **nie kopiować pól tożsamości**:
- `name`
- `inherits`
- `print_settings_id`

Kopiować tylko pola technologiczne.

---

## 11. Problem eksportu process preset w Orca

Sprawdzony bundle nie był uszkodzony jako ZIP ani JSON.

Roboczy wniosek:
- problem z eksportem process preset wynikał raczej z zachowania / ograniczenia / błędu Orca 2.3.x niż z uszkodzenia bundla

Praktyczna reguła:
- jeśli eksport procesu nie działa, najpierw importować bundle
- potem w Orca zrobić `Save As` dla procesu
- dopiero potem próbować eksportu

---

## 12. Ustalenie o procesie `0.08mm Ultra Quality`

Dodawany był proces:
- `0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle`

Założenia:
- proces jakościowy i bezpieczny
- bazowany na `0.15mm Quality`
- obniżone prędkości i akceleracje
- wymagał obniżenia `min_layer_height` w presecie drukarki z `0.15` do `0.08`

Dla wariantu `single`, jeśli proces 0.08 był kopiowany z `dual`, trzeba dopilnować:
- `support_filament = 0`
- `support_interface_filament = 0`

żeby nie zostały niepoprawne ustawienia z dual.

---

## 13. Finalne domyślne presety single i dual

### Dual
- `default_print_profile = "0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual"`
- `default_filament_profile = ["Z-PLA", "Z-SUPPORT"]`

### Single
- `default_print_profile = "0.15mm Quality @Zortrax Inventure 0.4 nozzle - single"`
- `default_filament_profile = ["Z-PLA"]`

To należy zachować jako docelowy stan organizacji presetów.

---

## 14. User presets vs system presets

Analizowano, czy bundle da się zrobić tak, aby preset pojawiał się w Orca jako **System Presets**, a nie **User Presets**.

Najuczciwszy wniosek:
- importowany `.orca_printer` pozostaje bundlem użytkownika
- nie należy zakładać, że samą zmianą JSON uda się go wiarygodnie przenieść do system presets

Aktualna decyzja projektowa:
- pozostawić bundle jako **user preset**
- dopracować domyślne procesy i filamenty

---

## 15. Firmware update Inventure

Do projektu wgrano różne wersje firmware update dla Inventure.

### Rozpoznana struktura pliku update

Każdy `InventureUpdate.bin` ma format:
- `0x00..0x03` -> `ZRTX`
- `0x04..0x07` -> `UINV`
- `0x08..0x0C` -> `rNNNN`
- `0x0D..0x10` -> stałe pole `225`
- `0x11..0x14` -> długość payloadu
- `0x15..EOF` -> jeden payload

### Rozpoznane rewizje

- `r0155` -> 1.2.0
- `r0207` -> 1.2.1
- `r0219` -> 1.2.2
- `r0232` -> 1.3.1
- `r0279` -> 1.4.0
- `r0300` -> 1.5.1
- `r0309` -> 1.5.4
- `r0323` -> 1.6.1

### Najważniejszy wniosek o payloadzie

Payload:
- ma bardzo wysoką entropię
- jest podzielny przez 16
- nie zawiera jawnych stringów
- nie wygląda jak ZIP / gzip / LZMA / ELF
- nie ma prostych powtarzających się bloków 16B / 32B

Najbardziej prawdopodobny model:
- payload jest szyfrowany albo opakowany w sposób dający efekt szyfrowania
- możliwy układ:
  - 16 B nagłówka kryptograficznego / IV / nonce
  - ciphertext
  - 16 B tag / MAC

Wniosek praktyczny:
- z plików firmware update **nie udało się jeszcze bezpośrednio wydobyć**:
  - komend drukarki
  - map materiałów
  - dodatkowych offsetów do patchera

To pozostaje nierozwiązane.

---

## 16. Ustalenia dotyczące profili i parametrów z Z-Suite

Dla jednego z referencyjnych ustawień Z-Suite zostały odczytane parametry:
- wersja aplikacji `2.32.0.0`
- szacowany czas druku `6h 16m`
- użycie materiału `19.81m (56g)`
- drukarka `Zortrax Inventure`
- support `Automatic`
- support angle `30°`
- materiał `Z-PLA`
- dysza `0.4 mm`
- warstwa `0.15 mm`
- jakość `High`
- infill `50%`

To jest użyteczny punkt odniesienia przy porównaniach z profilem Orca i plikami `.zcode` generowanymi przez Z-Suite.

---

## 17. Workflow Windows

Wersja windowsowa była punktem wyjścia i działała poprawnie.

Kluczowe elementy:
- `g2z.jar`
- wrapper Pythona oparty o `g2z_hybrid_wrapper_v10_orca_outdir_named.py`
- launcher `.bat`

Na Windows działało:
- uruchomienie `java -jar g2z.jar`
- patchowanie po konwersji
- nadawanie nazw plikom wynikowym na podstawie metadanych Orca

---

## 18. Workflow macOS Sequoia — ustalenia i problem

### 18.1. Cel portu na macOS

Na bazie działającego zestawu Windows przygotowano odpowiedniki dla macOS:
- `g2z_wrapper_macos.py`
- `run_orca_macos.sh`
- `run_orca_macos.command`

Założenie było takie:
- Orca wywołuje `.command` jako post-processing script
- `.command` uruchamia `.sh`
- `.sh` uruchamia wrapper Pythona i przekazuje ścieżkę do pliku `*.gcode.pp`
- wrapper uruchamia `g2z.jar`, a następnie patchuje wynikowy `.zcode`

### 18.2. Co działało na macOS

Potwierdzone:
- skrypt startował
- Python był znajdowany poprawnie
- wrapper był uruchamiany
- ścieżki do `g2z.jar` i wrappera były rozpoznawane
- log był zapisywany do `orca_postprocess_last.log`

### 18.3. Główny problem na macOS

Najważniejszy wykryty problem:
- aplikacja GUI Orca uruchamia skrypt z bardzo ubogim `PATH`
- w logu było widać:
  - `PATH: /usr/bin:/bin:/usr/sbin:/sbin`
- przez to skrypt znajdował **`/usr/bin/java`**, czyli systemowy stub Apple, zamiast prawdziwej Javy z Homebrew
- skutek:
  - `Unable to locate a Java Runtime`
  - `g2z.jar` nie startował
  - Orca kończyła post-processing błędem `Error code: 1`

### 18.4. Poprawna diagnoza

To oznaczało:
- problem **nie był** w samym wrapperze patchującym `.zcode`
- problem **nie był** w nazwach `g2z.jar` i `g2z_wrapper_macos.py`
- problem był w wykrywaniu i użyciu **niewłaściwej ścieżki do Javy**

### 18.5. Wniosek projektowy dla macOS

Na macOS launcher nie może polegać wyłącznie na:
- `java`
- `which java`
- `command -v java`

bo z GUI Orca może to zwrócić stub `/usr/bin/java`.

Launcher musi:
1. sprawdzać typowe ścieżki Homebrew, np.:
   - `/opt/homebrew/opt/openjdk/bin/java`
   - `/usr/local/opt/openjdk/bin/java`
2. sprawdzać wersje `openjdk@...`, jeśli występują
3. testować każdą znalezioną ścieżkę przez `java -version`
4. odrzucać ścieżki, które zwracają komunikat o braku runtime
5. dopiero na końcu używać fallbacków typu `command -v java`

### 18.6. Reguła praktyczna dla przyszłych wersji launcherów macOS

Wersje macOS powinny zachować nazewnictwo:
- `g2z_wrapper_macos.py`
- `run_orca_macos.sh`
- `run_orca_macos.command`

bez dodawania kolejnych suffixów typu `v2`, `v3`, żeby uniknąć chaosu nazw i rozjazdu odwołań między plikami.

Każdorazowo trzeba sprawdzić, że:
- `run_orca_macos.command` wywołuje `run_orca_macos.sh`
- `run_orca_macos.sh` odwołuje się do `g2z_wrapper_macos.py`
- `run_orca_macos.sh` odwołuje się do `g2z.jar`

---

## 19. Najważniejsze reguły spójności nazw plików

To jest krytyczne dla wszystkich kolejnych generacji plików:

### Reguła 1
Nie wprowadzać nowego nazewnictwa bez potrzeby.

### Reguła 2
Jeżeli plik nazywa się:
- `run_orca_macos.command`

to wewnątrz ma uruchamiać dokładnie:
- `run_orca_macos.sh`

### Reguła 3
Jeżeli plik nazywa się:
- `run_orca_macos.sh`

to wewnątrz ma odwoływać się dokładnie do:
- `g2z_wrapper_macos.py`
- `g2z.jar`

### Reguła 4
Nie mieszać jednocześnie kilku równoległych wersji w tym samym katalogu, jeśli celem jest szybkie uruchomienie z Orca.

---

## 20. Pliki i artefakty, które były ważne w projekcie

W rozmowie i plikach projektu pojawiały się m.in.:
- `g2z.jar`
- `g2z_hybrid_wrapper_v10_orca_outdir_named.py`
- `g2z_wrapper_macos.py`
- `run_orca_macos.sh`
- `run_orca_macos.command`
- `InventureUpdate.bin`
- testowe pliki `.zcode` z Z-Suite i po patchowaniu
- pliki `.orca_printer`
- archiwa ZIP z presetami i źródłami
- wcześniejsze pliki transferowe `.md`

Najważniejsze roboczo pozostają:
- aktywna logika patchera
- finalna logika bundla Orca
- właściwa obsługa single / dual
- poprawny launcher macOS z wykrywaniem realnej Javy

---

## 21. Co jest potwierdzone, a co nadal otwarte

### 21.1. Potwierdzone

- CRC nagłówka
- znaczenie podstawowych offsetów nagłówka
- logika `58..60`
- mapowanie `BASF Ultrafuse BVOH -> 0x17`
- logika Z-SUPPORT family -> `01 03 00`
- poprawność 1-stopniowego i 2-stopniowego patchowania w testach
- poprawność strukturalna finalnych bundle dla Orca
- przyczyna błędu post-processingu na macOS: wybór stubu `/usr/bin/java` w środowisku GUI Orca

### 21.2. Otwarte / nierozwiązane

- pełne znaczenie wszystkich nieudokumentowanych bajtów nagłówka poza potwierdzonymi polami
- pełne znaczenie pola stałego `225` w firmware update
- odszyfrowanie / rozpakowanie payloadu firmware
- pełna lista nieznanych komend firmware Inventure
- wszystkie przypadki, w których drukarka zgłasza błędy materiału mimo poprawnego CRC
- ostateczna finalna wersja launchera macOS po pełnym teście end-to-end z prawdziwą ścieżką do Javy z Homebrew

---

## 22. Najważniejsze reguły dalszej pracy

1. Nie wyciągać wniosków z porównań nieekwiwalentnych plików.
2. Przy analizie materiałów skupiać się najpierw na:
   - `62`
   - `85`
   - `58..60`
   - CRC
3. Przy pracy na `.orca_printer` zawsze utrzymywać spójność:
   - nazwy
   - ID
   - pliki
   - `bundle_structure.json`
4. Dla single procesy nie mogą zachowywać ustawień support filament z dual.
5. Dla Inventure wspólny bundle z 2 drukarkami jest preferowanym wariantem.
6. Na macOS nie ufać ślepo `java` z PATH aplikacji GUI; wykrywać prawdziwy runtime Java.
7. Przy generowaniu plików dla macOS zachować jedno, stabilne nazewnictwo bez mnożenia wersji nazw.

---

## 23. Krótki prompt startowy do nowego chatu

Można wkleić taki tekst:

> Pracujemy nad Zortrax Inventure.
>
> Zachowaj ten kontekst:
> - aktywna logika patchera wywodzi się z `g2z_hybrid_wrapper_v10_orca_outdir_named.py`
> - potwierdzone offsety nagłówka `.zcode`: 54..57, 61, 62, 63, 64, 65, 66, 68..71, 73..74, 77..78, 85, 127
> - bajty 58..60 to triplet trybu zadania:
>   - single i BASF BVOH -> `01 02 01`
>   - Z-SUPPORT / Z-SUPPORT Plus / Z-SUPPORT Premium -> `01 03 00`
> - BASF Ultrafuse BVOH ma kod `0x17`
> - CRC jest liczone poprawnie
> - finalny bundle Orca to 1 bundle z 2 drukarkami (`single`, `dual`), 8 processami i wspólnymi filamentami
> - defaulty:
>   - dual: `0.15 Quality`, `Z-PLA`, `Z-SUPPORT`
>   - single: `0.15 Quality`, `Z-PLA`
> - firmware update Inventure ma rozpoznany kontener `ZRTXUINVrNNNN`, ale payload pozostaje nieodczytany
> - na macOS GUI Orca ma ubogi PATH i może wybierać stub `/usr/bin/java`; launcher musi wykrywać prawdziwą Javę z Homebrew
> - przy dalszej analizie nie wolno porównywać nieekwiwalentnych plików i wyciągać z tego wniosków o polach nagłówka.

---

## 24. Najkrótsze streszczenie

Jeśli trzeba przenieść tylko minimum:

- aktywna logika patchera opiera się na wrapperze `g2z_hybrid_wrapper_v10_orca_outdir_named.py`
- `58..60`:
  - single + BASF BVOH -> `01 02 01`
  - Z-SUPPORT family -> `01 03 00`
- `62` = model material
- `85` = support material
- `127` = CRC i jest liczone poprawnie
- `BASF Ultrafuse BVOH = 0x17`
- finalny bundle Orca: 2 drukarki (`single`, `dual`), 8 processów, wspólne filamenty
- defaulty:
  - dual = `0.15 Quality`, `Z-PLA`, `Z-SUPPORT`
  - single = `0.15 Quality`, `Z-PLA`
- firmware update ma znany kontener, ale nieznany payload
- na macOS Orca GUI może wybierać stub `/usr/bin/java`, więc launcher musi wykrywać prawdziwą Javę
- nie wyciągać wniosków z porównań nieekwiwalentnych plików



## A16. `ZORTRAX_INVENTURE_chat_logic_i_ustalenia.md`

# Zortrax Inventure / OrcaSlicer — logika chatu i ustalenia do przeniesienia

Ten plik ma przenieść **cały istotny stan rozmowy** do innego chatu, tak aby można było kontynuować pracę bez odtwarzania kontekstu od zera.

---

## 1. Główny kontekst projektu

Użytkownik pracuje na presetach **OrcaSlicer** dla drukarki **Zortrax Inventure 0.4 nozzle** i modyfikuje pliki typu `.orca_printer`.

Celem było:
- diagnozowanie problemów z eksportem **process preset** w Orca,
- scalanie ustawień między presetami procesu,
- dodawanie nowych presetów procesu,
- poprawianie nazw filamentów i spójności wpisów w bundlu,
- utrzymywanie archiwów `.orca_printer` w stanie zgodnym z wewnętrzną strukturą Orca.

---

## 2. Najważniejsze ustalenie diagnostyczne: dlaczego Orca nie chce eksportować process preset

Sprawdzony plik `.orca_printer` **nie był uszkodzony jako archiwum ZIP**.

Ustalenie:
- `bundle_structure.json` był poprawny,
- JSON-y w `printer/`, `process/` i `filament/` parsowały się poprawnie,
- problem najpewniej **nie wynikał z uszkodzenia pliku**, tylko z tego, jak Orca traktuje procesy przy eksporcie.

Wniosek roboczy z analizy:
- procesy zapisane w bundlu są pełnymi presetami,
- Orca przy eksporcie **user process preset** oczekuje bardziej lokalnego / różnicowego formatu,
- problem jest zgodny z zachowaniem/bugiem OrcaSlicer 2.3.x,
- szczególnie podejrzane były procesy dziedziczące po innym procesie, ale niebędące zapisane jako typowy lokalny custom preset.

Praktyczny wniosek do dalszej pracy:
- jeśli eksport presetów procesu nadal nie działa, **najpierw importować printer bundle, potem w Orca zrobić „Save As” dla procesu**, a dopiero potem próbować eksportu,
- przy ręcznym patchowaniu bundle trzeba dbać o spójność nazw, identyfikatorów i wpisów w `bundle_structure.json`.

---

## 3. Ustalenie dotyczące scalania procesu `-20` do głównego procesu

Polecenie użytkownika:
- skopiować wszystkie odmienne pola z:
  - `0.15mm Quality @Zortrax Inventure 0.4 nozzle -20`
- do:
  - `0.15mm Quality @Zortrax Inventure 0.4 nozzle`

### Zasada scalania
Porównano oba presety i skopiowano **tylko pola ustawień roboczych**, a **nie pola tożsamości presetu**.

### Pola, których nie wolno kopiować przy takim scalaniu
Nie kopiować:
- `name`
- `inherits`
- `print_settings_id`

Powód:
- te pola definiują tożsamość i relację presetu,
- nadpisanie nimi głównego procesu mogłoby zamienić go w wariant zależny albo uszkodzić logikę bundla.

### Pola robocze, które zostały przeniesione podczas scalenia
Skopiowane różniące się ustawienia:
- `bottom_surface_pattern`
- `brim_type`
- `brim_width`
- `initial_layer_infill_speed`
- `initial_layer_speed`
- `internal_solid_infill_pattern`
- `raft_first_layer_density`
- `skirt_loops`
- `skirt_speed`
- `slowdown_for_curled_perimeters`
- `sparse_infill_density`
- `sparse_infill_pattern`
- `support_base_pattern_spacing`
- `support_interface_pattern`
- `support_interface_speed`
- `support_speed`
- `support_style`
- `top_surface_pattern`
- `travel_speed`

W jednym z etapów padła liczba **22 różniących się pól**, z czego **3 były polami identyfikującymi preset**, więc kopiowano tylko ustawienia użytkowe.

---

## 4. Ustalenie dotyczące nowego procesu `0.08`

Użytkownik poprosił o dorobienie procesu `0.08` do zestawu z zachowaniem nazewnictwa i uzupełnienie go sensownymi parametrami dla konfiguracji Zortrax Inventure 0.4.

### Zasada tworzenia procesu 0.08
Nowy preset został przygotowany:
- jako kopia dopracowanego `0.15mm Quality @Zortrax Inventure 0.4 nozzle`,
- z zachowaniem stylu nazewnictwa presetów,
- z bezpiecznym, jakościowym tuningiem zamiast agresywnych parametrów.

### Nazwa nowego procesu
- `0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle`

### Kluczowe zmiany w procesie 0.08
- `layer_height = 0.08`
- pierwszy layer pozostawiony na `0.20` dla przyczepności

### Prędkości ustawione konserwatywnie
- outer wall: `20`
- inner wall: `30`
- internal solid infill: `30`
- sparse infill: `35`
- top surface: `18`
- support: `18`
- support interface: `16`
- initial layer: `8`

### Przyspieszenia obniżone dla jakości
- default: `350`
- inner wall: `350`
- outer wall: `250`
- top surface: `220`
- sparse infill: `400`

### Powłoki dla jakości powierzchni
- `top_shell_layers = 11`
- `bottom_shell_layers = 9`

### Support
- `support_bottom_z_distance = 0.08`

### Bardzo ważna dodatkowa zmiana
W profilu drukarki trzeba było zmienić:
- `min_layer_height` z `0.15` na `0.08`

Powód:
- bez tego nowy proces 0.08 byłby sprzeczny z ograniczeniami printer presetu.

### Wniosek praktyczny
Ten preset 0.08 jest traktowany jako:
- **bezpieczny jakościowo**, nie ekstremalnie szybki,
- dobry do pierwszych testów,
- sensowny szczególnie dla małych modeli i ostrożnych prób.

---

## 5. Ustalenie dotyczące nazwy filamentu `External PEEK @INVENTURE`

Użytkownik poprosił o poprawkę nazwy filamentu:
- z `External PEEK @INVENTURE`
- na `External PEEK`

### Zasada tej poprawki
Nie wystarczy zmienić samej nazwy widocznej w jednym JSON.
Trzeba zachować spójność całego bundla.

### Elementy, które należy zmienić równocześnie
Przy takiej zmianie trzeba poprawić:
- `name`
- `filament_settings_id`
- nazwę pliku JSON filamentu
- wpis w `bundle_structure.json`
- ewentualne inne referencje tekstowe do starej nazwy

### Reguła kontroli po zmianie
Po patchu należy sprawdzić, czy w całym archiwum **nie został żaden wpis** zawierający:
- `External PEEK @INVENTURE`

Tę samą poprawkę wykonano potem ponownie dla kolejnego zestawu plików.

---

## 6. Reguły pracy z plikami `.orca_printer`

Przy kolejnych zmianach trzeba trzymać się następujących zasad:

### 6.1. `.orca_printer` traktować jako archiwum ZIP
Należy kontrolować:
- poprawność otwierania archiwum,
- poprawność JSON-ów,
- zgodność wpisów z `bundle_structure.json`.

### 6.2. Przy zmianach nazw presetów pilnować spójności bundla
Zmiana nazwy presetu zwykle wymaga poprawienia:
- nazwy w samym JSON,
- identyfikatora typu `*_settings_id`,
- nazwy pliku presetowego,
- wpisu w `bundle_structure.json`,
- ewentualnych powiązanych odwołań.

### 6.3. Przy scalaniu presetów nie kopiować pól tożsamości
Zasada ogólna:
- kopiować parametry technologiczne,
- nie kopiować pól identyfikujących preset lub relacje dziedziczenia, jeśli celem jest tylko przeniesienie ustawień.

Szczególnie uważać na pola typu:
- `name`
- `inherits`
- `print_settings_id`
- analogiczne pola ID w innych typach presetów

### 6.4. Przy dodawaniu nowego procesu sprawdzać ograniczenia printera
Jeżeli nowy proces używa warstwy mniejszej niż aktualne minimum drukarki, trzeba też poprawić odpowiednie ograniczenie w presecie drukarki, np.:
- `min_layer_height`

### 6.5. Preferencja użytkownika
Użytkownik oczekuje raczej:
- zmian praktycznych i gotowych do testu,
- zachowania nazewnictwa zgodnego z istniejącym zestawem,
- parametrów bezpiecznych i sensownych dla Zortrax Inventure,
- unikania zbędnych zmian poza zakresem polecenia.

---

## 7. Pliki wygenerowane lub modyfikowane w tej rozmowie

W toku rozmowy powstały lub były przygotowane m.in. następujące pliki wynikowe:

1. `Zortrax Inventure 0.4 nozzle_merged_main_process.orca_printer`
   - główny proces `0.15mm Quality...` uzupełniony o różniące się pola z wariantu `-20`

2. `Zortrax Inventure 0.4 nozzle_OK2_with_0.08.orca_printer`
   - dodany nowy proces `0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle`
   - zmienione `min_layer_height` na `0.08`

3. `Zortrax Inventure 0.4 nozzle_filament_name_fixed.orca_printer`
   - poprawiona nazwa filamentu `External PEEK`

4. `Zortrax Inventure 0.4 nozzle_filament_name_fixed_again.orca_printer`
   - ponownie wykonana ta sama poprawka dla kolejnego zestawu

5. `Zortrax_Inventure_all_attachments.zip`
   - ZIP ze wszystkimi załącznikami z rozmowy

6. `USTALENIA_Zortrax_Inventure_transfer.txt`
   - tekstowy skrót ustaleń do przeniesienia

7. ten plik:
   - `ZORTRAX_INVENTURE_chat_logic_i_ustalenia.md`

---

## 8. Preferowana logika dalszej rozmowy w nowym chacie

Jeśli praca ma być kontynuowana w innym czacie, warto przyjąć następujący tryb działania:

1. Najpierw wskazać, **na którym konkretnie pliku `.orca_printer` pracujemy**.
2. Potem określić typ operacji:
   - diagnostyka,
   - zmiana nazwy,
   - scalenie presetów,
   - dodanie nowego procesu,
   - usunięcie presetów,
   - naprawa spójności bundla.
3. Przy każdej zmianie sprawdzać:
   - zgodność JSON,
   - zgodność wpisów z `bundle_structure.json`,
   - brak osieroconych odwołań.
4. Jeśli powstaje nowy preset procesu, zachować:
   - dotychczasowe nazewnictwo,
   - styl parametrów zgodny z istniejącymi presetami,
   - ostrożny tuning dla Inventure 0.4.
5. Jeśli użytkownik chce eksportować preset procesu z Orca, pamiętać, że problem może wynikać z samej logiki Orca, a nie z uszkodzenia bundla.

---

## 9. Krótki prompt startowy do wklejenia w nowym chacie

Poniższy tekst można wkleić na start nowego chatu:

> Pracujemy na plikach `.orca_printer` dla `Zortrax Inventure 0.4 nozzle`.
> 
> Ustalenia z poprzedniego chatu:
> - bundle zwykle jest poprawny jako ZIP i JSON, a problem z eksportem process preset w Orca wynika raczej z formatu/buga Orca niż z uszkodzenia pliku,
> - przy scalaniu procesu `0.15mm Quality ... -20` do głównego procesu kopiujemy tylko parametry technologiczne, nie kopiujemy `name`, `inherits`, `print_settings_id`,
> - był już tworzony preset `0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle` na bazie `0.15mm Quality`, z bezpiecznymi parametrami jakościowymi oraz zmianą `min_layer_height` drukarki na `0.08`,
> - przy zmianie nazwy filamentu `External PEEK @INVENTURE` na `External PEEK` trzeba zmienić jednocześnie `name`, `filament_settings_id`, nazwę pliku JSON, wpisy w `bundle_structure.json` i sprawdzić brak starych referencji,
> - przy każdej zmianie trzeba utrzymywać spójność całego bundla.
> 
> Kontynuujmy od tego stanu.

---

## 10. Najkrótsza wersja ustaleń

Jeśli trzeba przenieść tylko minimum informacji:

- To nie był problem uszkodzonego ZIP/JSON, tylko raczej ograniczenie/bug Orca przy eksporcie process preset.
- Przy scalaniu presetów kopiować tylko ustawienia technologiczne, nie pola identyfikujące preset.
- Dla procesu 0.08 trzeba także obniżyć `min_layer_height` w printer presecie.
- Zmiana nazwy filamentu wymaga poprawienia także ID, nazwy pliku i `bundle_structure.json`.
- Najważniejsza zasada: zawsze pilnować spójności bundla `.orca_printer`.



## A17. `ZORTRAX_INVENTURE_deep_thread_summary_2026-04-17.md`

# ZORTRAX INVENTURE / ORCA POST-PROCESS — deep transfer summary for future chats

Date: 2026-04-17  
Scope: OrcaSlicer → G-code → pure-Python `.zcode` conversion for **Zortrax Inventure**, current launcher logic for **Windows** and **macOS**, progress rendering, Orca output-path behavior, and the latest accepted rules after multiple test iterations.

---

## 1. What this summary is for

This file is meant to transfer the **full current working state** of the thread into another chat, without having to reconstruct decisions from earlier experiments.

It focuses on the part of the project that ended up as the **current active post-processing path**:

- **pure-Python converter only**,
- **no Java**,
- **no `g2z.jar`**, 
- output path taken from **Orca environment** when slicing through Orca,
- no old `out` directory fallback,
- current progress/logging behavior,
- Windows and macOS launcher behavior,
- what was tested and what was explicitly rejected.

This is not only a summary of files, but also a summary of **why specific versions were kept or discarded**.

---

## 2. Short current state

### Current direction
The project moved away from the older hybrid path:

`Orca -> G-code -> g2z.jar -> patch header`

toward the current path:

`Orca -> G-code -> pure-Python converter -> patched classic .zcode`

### Current high-level decisions
The latest accepted direction is:

1. **Do not use Java** in the active workflow.
2. **Do not use `g2z.jar`** in the active workflow.
3. **Do not keep compare/reference JAR code** in the active workflow.
4. **Do not use old `C:\OrcaScripts\out` fallback** for Orca `.gcode.pp` jobs.
5. For Orca temporary `.gcode.pp` input, write output to the **final Save / Save As path provided by Orca environment**.
6. On **Windows**, visible progress in console is useful and desired.
7. On **macOS**, it is acceptable to keep processing **silent in background** and use the log file instead of forcing Terminal to open.
8. Home-directory based launcher lookup (`~/OrcaScripts` or `%USERPROFILE%\OrcaScripts`) was prepared as a **test launcher option**, not as an automatic converter behavior change.

---

## 3. Current main files

### Current converter package to treat as the cleanest active basis
The cleanest current package is:

- `Zortrax_Inventure_Orca_pure_python_nojava_nofallback_package.zip`

Inside it:
- `g2z_wrapper_orca.py`
- `run_g2z_orca_postprocess.bat`
- `run_g2z_orca_postprocess.sh`
- `run_g2z_orca_postprocess.command`
- `README.txt`

This package reflects the deliberate cleanup where:
- Java references were removed,
- `g2z.jar` references were removed,
- old output-folder fallback for Orca temp input was removed.

### Additional launcher-only test package
A separate test package was created for **home directory launcher resolution**:

- `Zortrax_Inventure_home_dir_test_launchers.zip`

These launchers were intended only to test whether the launcher should prefer:
- Windows: `%USERPROFILE%\OrcaScripts`
- macOS: `$HOME/OrcaScripts`

before falling back to the launcher directory.

Important: that package changed **launcher lookup behavior**, not the actual converter logic.

---

## 4. Current converter behavior

### 4.1. Active conversion model
The current active converter is a **pure-Python classic `.zcode` path**.

That means:
- it reads Orca G-code,
- parses metadata,
- optionally prepares a work copy when `M83` / relative extrusion needs conversion into the accepted internal style,
- generates classic `.zcode` in Python,
- patches confirmed Inventure header fields,
- recalculates CRC.

### 4.2. What was removed on purpose
The active converter should no longer contain:
- `java`
- `g2z.jar`
- compare-with-jar path
- jar fallback path
- jar-related CLI flags
- output fallback to `C:\OrcaScripts\out` for Orca `.gcode.pp`

### 4.3. Manual direct-input behavior
There is one important distinction that remains intentional:

For **manual direct `.gcode` input** used outside Orca:
- output is still allowed next to the input file,
- or via explicit `--output`, if provided.

This is not treated as the removed Orca fallback.  
The removed fallback was specifically the old behavior of saving Orca temp `.gcode.pp` jobs into a fixed `out` directory.

---

## 5. Orca output-path behavior — final current understanding

### 5.1. What the user wanted
The user wanted the converter to save the final `.zcode` **in the same place** where Orca saves `.gcode` via **Save / Save As**, if Orca provides that information.

### 5.2. What was found
After testing, it turned out that Orca may expose useful output information through environment variables.

The converter was updated to inspect environment variables such as:
- `SLIC3R_PP_OUTPUT_PATH`
- `ORCA_OUTPUT_PATH`
- `SLIC3R_PP_OUTPUT`
- `ORCA_OUTPUT`
- `SLIC3R_PP_OUTPUT_NAME`
- `ORCA_OUTPUT_NAME`

### 5.3. What was confirmed on Windows
A real Windows log confirmed that Orca provided a **full final path** through:
- `SLIC3R_PP_OUTPUT_NAME`

and the converter reported:
- output mode = `auto (SLIC3R_PP_OUTPUT_NAME full path)`
- final output path = actual Save / Save As location in the user’s Downloads folder

This means the auto-output mode is not only theoretical — it was **confirmed in practice**.

### 5.4. Final rule now
For Orca temporary `.gcode.pp` input:
- the converter **must** use the final path from Orca environment,
- if Orca does **not** provide that path, the converter should stop with a clear error,
- it should **not** silently fall back to a fixed `out` directory anymore.

This is one of the most important final decisions from the latest phase of the thread.

---

## 6. Current status of old `out` directory references

### 6.1. Project-level reality
Earlier packages used:
- `C:\OrcaScripts\out`
- `--out-dir`
- launchers with explicit fallback output folders

These existed in several intermediate packages.

### 6.2. Current accepted package state
In the cleaned `final_nojava` package:
- there is **no old `C:\OrcaScripts\out` output path**,
- there is **no Orca `.gcode.pp` fallback to out-dir**,
- there is **no active `--out-dir` fallback for Orca temp input**.

### 6.3. Important practical warning
If the user still has old scripts mixed in `C:\OrcaScripts`, references to old `out` logic may survive in:
- older `.bat`
- older `.sh`
- older `.command`
- older copies of `g2z_wrapper_orca.py`

So the correct rule is:
- the **clean current package** has no old `out` behavior,
- but the user’s local directory may still contain old scripts if not fully replaced.

---

## 7. Progress display — what happened and what should be remembered

### 7.1. Original request
The user wanted the converter to show:
- what it is currently doing,
- progress percent,
- with a cleaner console presentation.

Later, the user explicitly requested a format where:
- current step is shown in one line,
- progress is shown in another line,
- percent updates should not constantly push the console downward.

### 7.2. What was tried
Several progress renderers were tested:

1. **Simple multi-line prints**  
   - easy to implement,
   - but noisy,
   - not visually stable.

2. **2-line dashboard with cursor movement / re-draw**  
   - looked nicer in theory,
   - but caused instability and console rendering issues in some environments.

3. **Stable step line + progress line with safer update logic**  
   - this became the preferred direction.

### 7.3. What went wrong during iterations
There were regressions where:
- progress disappeared in later versions,
- output became visually broken,
- percentages appeared to go down and then up,
- ordinary messages were appended to the active progress line,
- PowerShell + `Tee-Object` caused ugly spaced-out output,
- Windows console encoding caused Unicode rendering crashes.

### 7.4. Unicode issue on Windows
A concrete Windows error was found:
- console code page was effectively `cp1250`,
- the wrapper used Unicode characters such as `↳`,
- Python failed with `UnicodeEncodeError`.

This led to the final rule:
- console output must use **Unicode-safe fallback behavior**,
- pretty glyphs must be optional,
- ASCII fallback must be automatic.

### 7.5. Current accepted approach
The accepted direction is:
- visible progress on Windows is useful,
- progress should be stable and not wreck the console,
- Unicode must not break execution,
- if a truly dynamic dashboard is unstable in a given terminal, the script should degrade gracefully.

The exact renderer evolved multiple times, but the lesson to carry forward is more important than any one intermediate version:

> The project values **stable, readable progress output** more than clever terminal tricks.

---

## 8. Logging — what is required

### 8.1. Why logging matters
The user explicitly wanted visible progress, but when UI behavior differed across systems, the log file became the reliable fallback.

### 8.2. Required log behavior
Current expected logging behavior:

- **Windows**: log file in `OrcaScripts`, typically
  - `C:\OrcaScripts\orca_postprocess_last.log`

- **macOS**: log file next to the scripts, typically
  - `orca_postprocess.log`
  - unless `G2Z_LOG_FILE` is explicitly set

### 8.3. Regression that happened
At one stage, after other changes were introduced, the log file disappeared from the launcher path. This was treated as a regression and had to be restored.

### 8.4. Current rule
Even if console visualization changes, **logging must stay available**.

---

## 9. Windows launcher evolution and current lessons

### 9.1. What worked poorly
These approaches caused problems and should be remembered as undesirable unless there is a very specific reason:
- PowerShell wrapping around Python just to mirror output,
- `Tee-Object` for live log mirroring,
- complicated output piping,
- anything that distorts console text or hides progress.

### 9.2. Why
PowerShell wrapping introduced visible output artifacts, including heavily spaced-out lines like:
- `G e n e r a t e d ...`
- `P a t c h e d ...`

The converter was actually working; the launcher presentation was the problem.

### 9.3. Current Windows launcher preference
Current best practice from this thread:
- keep the Windows `.bat` simple,
- use `py -3 -u` or `python -u` for unbuffered output,
- avoid PowerShell as a wrapper unless absolutely necessary,
- let the wrapper itself manage the progress/log behavior.

### 9.4. Home-directory launcher test for Windows
A test launcher version was prepared with logic:
1. prefer `%USERPROFILE%\OrcaScripts`
2. if not found, use launcher directory
3. fallback order in detecting user home:
   - `USERPROFILE`
   - `HOMEDRIVE` + `HOMEPATH`
   - `HOME`

This is useful if the user wants the startup script to find the home-based script folder automatically.

Important: it was explicitly described as a **test launcher**.

---

## 10. macOS launcher evolution and current lessons

### 10.1. What was tested
A test was made to force macOS to open Terminal.app and show post-processing live.

This used AppleScript / `osascript` and a wrapper approach intended to:
- open Terminal window,
- display progress,
- wait for conversion to finish,
- return a proper exit code to Orca.

### 10.2. User decision
This was explicitly marked as **test-only** and then rejected as unnecessary.

Final user preference:
- macOS may remain **without opening Terminal**,
- processing may run silently in the background,
- log file is enough.

### 10.3. Current macOS rule
Keep macOS simpler:
- `.sh` does the work,
- `.command` can stay a thin launcher to `.sh`,
- no forced Terminal window is required.

### 10.4. Home-directory launcher test for macOS
Test launchers were created with logic:
1. prefer `$HOME/OrcaScripts`
2. if not found, use launcher directory

Again, this is launcher lookup logic, not a converter behavior change.

---

## 11. How Post-processing path should be entered in Orca

### Final conclusion
Do **not** rely on writing shell variables directly inside the Orca Post-processing field, such as:
- `%USERPROFILE%\...`
- `$HOME/...`

The safer rule is:
- in Orca, enter a **full absolute path to the launcher file**,
- let the launcher itself resolve the home directory if needed.

### Practical examples
Windows:
- `C:\Users\<username>\OrcaScripts\run_g2z_orca_postprocess.bat`

macOS:
- `/Users/<username>/OrcaScripts/run_g2z_orca_postprocess.command`

If the launcher contains the home-aware logic, that is internal to the launcher — Orca still receives a normal absolute path.

---

## 12. What should be treated as final vs test-only

### Treat as current final direction
These points should be treated as the current accepted direction unless the user changes them later:

1. **Pure Python only**.
2. **No Java**.
3. **No `g2z.jar`**.
4. **No JAR compare path**.
5. **No old `out` fallback for Orca temp input**.
6. For Orca temp `.gcode.pp`, **require output path from Orca environment**.
7. **Windows** may show visible progress in console.
8. **macOS** may remain silent in background and rely on log file.
9. Logging must remain available.
10. Unicode in console must not be allowed to crash the converter.

### Treat as test-only / optional
These should not be mistaken for the current core production direction:

1. Forced Terminal opening on macOS.
2. PowerShell/Tee-based live logging on Windows.
3. Fancy unstable progress dashboards with aggressive cursor control.
4. Home-directory launcher package as a mandatory standard — it is currently a **test launcher option**, not yet declared the universal final launcher policy.

---

## 13. Important files and packages generated in this phase

### Main cleaned package
- `Zortrax_Inventure_Orca_pure_python_nojava_nofallback_package.zip`

### Home-directory launcher test package
- `Zortrax_Inventure_home_dir_test_launchers.zip`

### macOS terminal-visible test package
- `Zortrax_Inventure_macOS_terminal_visible_package.zip`

This last package should be remembered as **test-only**, not the default final direction.

---

## 14. Practical operational status to resume from

If work is resumed in another chat, the most accurate starting point is:

### Converter
Use the **clean pure-Python no-Java/no-fallback converter** as the main base.

### Launchers
There are two possible launcher tracks now:

#### A. Simple production-like launchers
Use the launchers from the cleaned no-Java package when you want the simplest current production-style behavior.

#### B. Home-aware launcher tests
Use the `home_test_package` launchers if you specifically want to test automatic discovery of:
- `%USERPROFILE%\OrcaScripts`
- `$HOME/OrcaScripts`

before falling back to the launcher directory.

### macOS terminal
Do not force Terminal to open unless explicitly requested again.

### Output path rule
For Orca `.gcode.pp`:
- output path must come from Orca environment,
- no silent fallback to `out`.

---

## 15. Open questions / possible next steps

The following points remain open for future work if needed:

1. Whether the **home-aware launcher behavior** should become the final default launcher behavior, or remain only a test option.
2. Whether progress refresh should be rate-limited more aggressively, for example every 2% or 5%, to reduce console flicker.
3. Whether the progress renderer should be simplified even further for maximum terminal stability.
4. Whether the converter should produce more structured log records in addition to human-readable output.
5. Whether manual direct `.gcode` mode should remain as-is or be tightened further.

---

## 16. Short transfer prompt for a new chat

You can paste the following into a new chat:

> We are continuing the Zortrax Inventure / Orca post-process work.
>
> Current state to preserve:
> - active workflow is now pure Python only
> - Java and g2z.jar were intentionally removed from the active converter and launchers
> - old Orca out-dir fallback was intentionally removed for Orca `.gcode.pp`
> - for Orca temp `.gcode.pp`, the converter must use the final Save / Save As path provided through Orca environment, otherwise it should fail clearly
> - this was confirmed on Windows using `SLIC3R_PP_OUTPUT_NAME` as a full final path
> - Windows may show visible progress in console
> - macOS may stay silent in background and rely on log file; forced Terminal opening was only a test and is not the preferred default
> - logging must remain available
> - Unicode console output must not crash the converter on Windows
> - the clean current package is `Zortrax_Inventure_Orca_pure_python_nojava_nofallback_package.zip`
> - a separate `Zortrax_Inventure_home_dir_test_launchers.zip` exists to test launchers that prefer `%USERPROFILE%\OrcaScripts` on Windows and `$HOME/OrcaScripts` on macOS
> - do not reintroduce Java, g2z.jar, compare-with-jar logic, or old `C:\OrcaScripts\out` fallback unless explicitly requested

---

## 17. Ultra-short version

- Current direction = **pure Python only**.
- **No Java**, **no `g2z.jar`**, **no JAR compare path**.
- For Orca `.gcode.pp`, use **Orca-provided final output path**.
- **No old `out` fallback** for Orca temp input.
- Windows: visible progress is useful.
- macOS: silent background mode is acceptable; no forced Terminal by default.
- Keep logging.
- Home-directory launchers were created as a **test option**.



## A18. `Zortrax_Inventure_full_transfer_summary_v1.2.7_2026-04-29.md`

# ZORTRAX INVENTURE / ORCA — pełne podsumowanie chatu i transfer wiedzy

Data: 2026-04-29  
Aktualny stan roboczy: **v1.2.7-e-speed-scale**  
Zakres: OrcaSlicer → G-code → pure Python `.zcode`, procedury startu, purge, toolchange, layer-clean, reverse engineering `.zcode`, nagłówka, opcode, preview `0x12`, materiały i praktyczne ustalenia z testów drukarki.

---

## 0. Do czego służy ten plik

Ten plik ma pozwolić kontynuować projekt w nowym chacie bez odtwarzania całej historii. Zawiera:

- aktualną logikę konwertera,
- finalne wpisy Orca Machine G-code dla **single** i **dual**,
- parametry markerów i ich znaczenie,
- potwierdzone bajty / komendy `.zcode`,
- procedury startowe i czyszczące ustalone z oryginalnych plików Z-Suite oraz testów fizycznych,
- mapowanie materiałów i ważne pola nagłówka,
- ustalenia o preview `opcode 0x12`,
- pułapki i rzeczy, których nie traktować już jako pewnik.

---

## 1. Najważniejszy aktualny stan projektu

Aktualna robocza wersja konwertera:

```text
v1.2.7-e-speed-scale
```

Najważniejsze wygenerowane pliki tej wersji:

```text
Zortrax_Inventure_Orca_converter_only_v1.2.7.zip
Zortrax_Inventure_Orca_v1.2.7_e_speed_scale.zip
Zortrax_Inventure_Orca_v1.2.7_e_speed_scale/g2z_wrapper_orca.py
Zortrax_Inventure_Orca_v1.2.7_e_speed_scale/ORCA_MACHINE_GCODE_v1.2.7.md
```

Stan praktyczny potwierdzony przez użytkownika:

```text
v1.2.7 wygląda, że działa OK.
```

Główna zmiana v1.2.7 względem v1.2.6:

```text
Dodano wspólne parametry E_SPEED_SCALE= oraz RETRACT_SPEED_SCALE=
dla START_MACHINE, TOOLCHANGE_CLEAN, LAYER_CLEAN i START_PURGE.
```

Cel tej zmiany:

- dla kruchego PVA/BVOH/Z-SUPPORT zmniejszyć prędkość purge/prime oraz retrakcji,
- nie zmieniać od razu długości purge,
- zachować ilość materiału potrzebną do odpowietrzenia/napełnienia dyszy,
- ograniczyć ryzyko zerwania kruchego filamentu.

---

## 2. Reguła numeracji wersji

Użytkownik ustalił:

```text
Nie robić kolejnych dużych iteracji typu 1.3 / 1.4 dla zmian cząstkowych.
Zmiany robocze mają dostawać numerację 1.2.1, 1.2.2, 1.2.3 itd.
Dopiero gdy użytkownik wyraźnie powie „zrób wersję produkcyjną”, można podnieść drugą cyfrę, np. do 1.3.
```

Aktualny ciąg istotnych wersji:

```text
v1.2.2  — rozdzielenie TOOLCHANGE_CLEAN i LAYER_CLEAN, potwierdzone testami single/dual.
v1.2.3  — temperatury z Orca przed purge + ooze prevention przy toolchange.
v1.2.4  — cichszy progress/log, poprawka PREHEAT_TIME=AUTO.
v1.2.5  — START_LAYER=2 dla LAYER_CLEAN, aby nie czyścić pierwszej warstwy po starcie.
v1.2.6  — SKIP_AFTER_TOOLCHANGE=1 dla LAYER_CLEAN, aby nie dublować purge po toolchange.
v1.2.7  — E_SPEED_SCALE= i RETRACT_SPEED_SCALE= dla kruchego PVA/BVOH/supportu.
```

---

## 3. Aktualna logika wysokiego poziomu

Projekt obsługuje workflow:

```text
OrcaSlicer -> G-code z ORCA METADATA -> post-process -> pure Python converter -> classic .zcode dla Zortrax Inventure
```

Obecny kierunek:

- aktywny konwerter jest pure Python,
- nie opiera się na `g2z.jar` w aktualnym workflow roboczym,
- generuje classic `.zcode`,
- patchuje / ustawia znane pola nagłówka,
- interpretuje specjalne markery `;ZORTRAX_*`,
- generuje procedury Z-Suite-like: start, purge, toolchange-clean, layer-clean, end.

Ważna zasada metodologiczna:

```text
Nie mieszać dwóch kategorii:
1. potwierdzone bajty / komendy powodujące konkretne ruchy,
2. kompletne procedury start/toolchange/end.
```

Wiele testów potwierdziło ruchy modułów, ale nie każdy układ modułów jest automatycznie finalną procedurą Z-Suite.

---

## 4. Najważniejsze markery v1.2.7

### 4.1. START_MACHINE

```gcode
;ZORTRAX_START_MACHINE SINGLE
;ZORTRAX_START_MACHINE DUAL
;ZORTRAX_START_MACHINE AUTO
```

W v1.2.7 można dodać:

```gcode
E_SPEED_SCALE=0.5
RETRACT_SPEED_SCALE=0.5
```

Przykład:

```gcode
;ZORTRAX_START_MACHINE DUAL E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5
```

`START_MACHINE` zawiera już start Z-Suite-like z purge/prime. Nie należy dodawać po nim `;ZORTRAX_START_PURGE`, bo spowoduje dodatkowy purge.

### 4.2. TOOLCHANGE_CLEAN

Marker do pola Orca Change filament / Tool change:

```gcode
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
```

W v1.2.7 zalecany wariant PVA-safe:

```gcode
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
```

Wymaga poprzedzającego bloku:

```gcode
;ZORTRAX_TOOLCHANGE_META previous_extruder=... next_extruder=... old_temp=... new_temp=...
```

### 4.3. LAYER_CLEAN

Marker do pola Orca Layer change G-code:

```gcode
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO TEMP=AUTO
```

W v1.2.7 zalecany wariant PVA-safe:

```gcode
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

Znaczenie:

```text
EVERY=5                  czyść co 5 warstw
START_LAYER=2            nie uruchamiaj layer clean na pierwszej drukowanej warstwie
SKIP_AFTER_TOOLCHANGE=1  nie uruchamiaj layer clean bezpośrednio po toolchange clean
PURGE=AUTO               dobierz profil purge/prime po materiale
TEMP=AUTO                ustaw i poczekaj na temperaturę aktywnej głowicy z Orca
E_SPEED_SCALE=0.5        skaluj prędkości E purge/prime
RETRACT_SPEED_SCALE=0.5  skaluj prędkość idle retract, jeśli występuje
```

### 4.4. START_PURGE

Stary marker:

```gcode
;ZORTRAX_START_PURGE AUTO LENGTH=20
```

W aktualnym zalecanym układzie zwykle **nie używać po `START_MACHINE`**, bo `START_MACHINE` ma już własne purge/prime.

Marker pozostaje użyteczny tylko do osobnych testów albo specjalnych ręcznych procedur.

---

## 5. E_SPEED_SCALE i RETRACT_SPEED_SCALE — logika v1.2.7

### 5.1. Co skaluje E_SPEED_SCALE

`E_SPEED_SCALE` skaluje tylko prędkości ruchów E używanych do purge/prime.

Przykładowo:

```text
F480  -> F240
F3600 -> F1800
F2100 -> F1050
F4800 -> F2400
```

Nie skaluje:

- ruchów XY,
- przejazdów po szczotkach,
- dojazdów do pozycji specjalnych,
- feedrate mechanicznego clean path.

### 5.2. Co skaluje RETRACT_SPEED_SCALE

`RETRACT_SPEED_SCALE` skaluje prędkość retrakcji starej / nieaktywnej głowicy, szczególnie:

```text
IDLE_RETRACT=AUTO = -20 mm @ F480
```

Przy `RETRACT_SPEED_SCALE=0.5`:

```text
F480 -> F240
```

Długość retrakcji nie zmienia się, jeśli nadal jest:

```gcode
IDLE_RETRACT=AUTO
```

### 5.3. Dlaczego dla PVA/BVOH najpierw zmniejszać prędkości, a nie długości

Dla kruchego PVA/BVOH/Z-SUPPORT problemem jest często zerwanie filamentu przy gwałtownym podawaniu albo retrakcji. Najbezpieczniejsza kolejność testów:

```text
Test 1: tylko E_SPEED_SCALE=0.5 i RETRACT_SPEED_SCALE=0.5
Test 2: jeśli nadal zrywa, IDLE_RETRACT=10 zamiast AUTO (-20 mm)
Test 3: jeśli nadal problem, dopiero zmniejszać całkowity purge
```

Nie zaleca się od razu zmniejszać każdego ruchu E o 10 mm, bo profile mają kilka ruchów E i można przypadkiem zabrać zbyt dużo materiału.

---

## 6. Finalne Machine G-code dla Orca v1.2.7

Poniższy blok jest kopią aktualnej instrukcji v1.2.7. Wariant zawiera `E_SPEED_SCALE=0.5` i `RETRACT_SPEED_SCALE=0.5`, czyli tryb bezpieczniejszy dla kruchego PVA/BVOH/supportu. Dla zwykłego PLA/ABS można usunąć te parametry albo ustawić `1.0`.

# Orca Machine G-code — Zortrax Inventure v1.2.7

Wariant poniżej jest ustawiony jako **PVA-safe / brittle support mode**, czyli z wolniejszymi ruchami E:

```text
E_SPEED_SCALE=0.5
RETRACT_SPEED_SCALE=0.5
```

Dla normalnych materiałów można te parametry usunąć albo ustawić `1.0`.

---

# DUAL

## File header G-code — DUAL

```gcode
; ===== ORCA METADATA BEGIN =====
; mode=DUAL
; process={print_preset}
; layer_height={layer_height}
; initial_layer_print_height={initial_layer_print_height}

; filament_t0={filament_preset[0]}
; filament_type_t0={filament_type[0]}
; filament_t1={filament_preset[1]}
; filament_type_t1={filament_type[1]}
; support_material={filament_preset[1]}
; support_material_type={filament_type[1]}

; support={enable_support}
; support_type={support_type}
; support_threshold_angle={support_threshold_angle}
; infill_density={sparse_infill_density}
; top_layers={top_shell_layers}
; bottom_layers={bottom_shell_layers}

; travel_speed={travel_speed}
; travel_speed_z={travel_speed_z}
; support_speed={support_speed}
; support_interface_speed={support_interface_speed}

; retraction_length_t0={retraction_length[0]}
; retraction_speed_t0={retraction_speed[0]}
; deretraction_speed_t0={deretraction_speed[0]}
; retract_restart_extra_t0={retract_restart_extra[0]}
; retract_length_toolchange_t0={retract_length_toolchange[0]}
; retract_restart_extra_toolchange_t0={retract_restart_extra_toolchange[0]}

; retraction_length_t1={retraction_length[1]}
; retraction_speed_t1={retraction_speed[1]}
; deretraction_speed_t1={deretraction_speed[1]}
; retract_restart_extra_t1={retract_restart_extra[1]}
; retract_length_toolchange_t1={retract_length_toolchange[1]}
; retract_restart_extra_toolchange_t1={retract_restart_extra_toolchange[1]}

; nozzle_temperature_t0={nozzle_temperature[0]}
; nozzle_temperature_t1={nozzle_temperature[1]}
; nozzle_temperature_initial_layer_t0={nozzle_temperature_initial_layer[0]}
; nozzle_temperature_initial_layer_t1={nozzle_temperature_initial_layer[1]}
; chamber_temperature_t0={chamber_temperature[0]}
; chamber_temperature_t1={chamber_temperature[1]}
; idle_temperature_t0={idle_temperature[0]}
; idle_temperature_t1={idle_temperature[1]}

; standby_temperature_delta={standby_temperature_delta}
; ooze_prevention={ooze_prevention}
; preheat_time={preheat_time}

; curr_bed_type={curr_bed_type}

; bed_temp_supertack_initial_t0={supertack_plate_temp_initial_layer[0]}
; bed_temp_supertack_initial_t1={supertack_plate_temp_initial_layer[1]}
; bed_temp_supertack_t0={supertack_plate_temp[0]}
; bed_temp_supertack_t1={supertack_plate_temp[1]}

; bed_temp_cool_initial_t0={cool_plate_temp_initial_layer[0]}
; bed_temp_cool_initial_t1={cool_plate_temp_initial_layer[1]}
; bed_temp_cool_t0={cool_plate_temp[0]}
; bed_temp_cool_t1={cool_plate_temp[1]}

; bed_temp_textured_cool_initial_t0={textured_cool_plate_temp_initial_layer[0]}
; bed_temp_textured_cool_initial_t1={textured_cool_plate_temp_initial_layer[1]}
; bed_temp_textured_cool_t0={textured_cool_plate_temp[0]}
; bed_temp_textured_cool_t1={textured_cool_plate_temp[1]}

; bed_temp_eng_initial_t0={eng_plate_temp_initial_layer[0]}
; bed_temp_eng_initial_t1={eng_plate_temp_initial_layer[1]}
; bed_temp_eng_t0={eng_plate_temp[0]}
; bed_temp_eng_t1={eng_plate_temp[1]}

; bed_temp_hot_initial_t0={hot_plate_temp_initial_layer[0]}
; bed_temp_hot_initial_t1={hot_plate_temp_initial_layer[1]}
; bed_temp_hot_t0={hot_plate_temp[0]}
; bed_temp_hot_t1={hot_plate_temp[1]}

; bed_temp_textured_initial_t0={textured_plate_temp_initial_layer[0]}
; bed_temp_textured_initial_t1={textured_plate_temp_initial_layer[1]}
; bed_temp_textured_t0={textured_plate_temp[0]}
; bed_temp_textured_t1={textured_plate_temp[1]}
; ===== ORCA METADATA END =====
```

## Machine start G-code — DUAL

```gcode
;ZORTRAX_START_MACHINE DUAL E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5
```

## Change filament / Tool change G-code — DUAL

```gcode
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400
```

## Layer change G-code — DUAL

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

## Machine end G-code — DUAL

```gcode
;ZORTRAX_END_MACHINE AUTO
```

---

# SINGLE

## File header G-code — SINGLE

```gcode
; ===== ORCA METADATA BEGIN =====
; mode=SINGLE
; process={print_preset}
; layer_height={layer_height}
; initial_layer_print_height={initial_layer_print_height}

; filament_t0={filament_preset[0]}
; filament_type_t0={filament_type[0]}

; support={enable_support}
; support_type={support_type}
; support_threshold_angle={support_threshold_angle}
; infill_density={sparse_infill_density}
; top_layers={top_shell_layers}
; bottom_layers={bottom_shell_layers}

; travel_speed={travel_speed}
; travel_speed_z={travel_speed_z}
; support_speed={support_speed}
; support_interface_speed={support_interface_speed}

; retraction_length_t0={retraction_length[0]}
; retraction_speed_t0={retraction_speed[0]}
; deretraction_speed_t0={deretraction_speed[0]}
; retract_restart_extra_t0={retract_restart_extra[0]}
; retract_length_toolchange_t0={retract_length_toolchange[0]}
; retract_restart_extra_toolchange_t0={retract_restart_extra_toolchange[0]}

; nozzle_temperature_t0={nozzle_temperature[0]}
; nozzle_temperature_initial_layer_t0={nozzle_temperature_initial_layer[0]}
; chamber_temperature_t0={chamber_temperature[0]}
; idle_temperature_t0={idle_temperature[0]}

; standby_temperature_delta={standby_temperature_delta}
; ooze_prevention={ooze_prevention}
; preheat_time={preheat_time}

; curr_bed_type={curr_bed_type}

; bed_temp_supertack_initial_t0={supertack_plate_temp_initial_layer[0]}
; bed_temp_supertack_t0={supertack_plate_temp[0]}

; bed_temp_cool_initial_t0={cool_plate_temp_initial_layer[0]}
; bed_temp_cool_t0={cool_plate_temp[0]}

; bed_temp_textured_cool_initial_t0={textured_cool_plate_temp_initial_layer[0]}
; bed_temp_textured_cool_t0={textured_cool_plate_temp[0]}

; bed_temp_eng_initial_t0={eng_plate_temp_initial_layer[0]}
; bed_temp_eng_t0={eng_plate_temp[0]}

; bed_temp_hot_initial_t0={hot_plate_temp_initial_layer[0]}
; bed_temp_hot_t0={hot_plate_temp[0]}

; bed_temp_textured_initial_t0={textured_plate_temp_initial_layer[0]}
; bed_temp_textured_t0={textured_plate_temp[0]}
; ===== ORCA METADATA END =====
```

## Machine start G-code — SINGLE

```gcode
;ZORTRAX_START_MACHINE SINGLE E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5
```

## Change filament / Tool change G-code — SINGLE

Zostawić puste.

## Layer change G-code — SINGLE

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

## Machine end G-code — SINGLE

```gcode
;ZORTRAX_END_MACHINE AUTO
```


---

## 7. Sekcje Orca, które zostawić puste

Dla single i dual, jeśli nie ma tam świadomie dodanych własnych procedur:

```text
Filament start G-code      puste
Filament end G-code        puste
Before layer change        puste
Time lapse G-code          puste
Pause G-code               puste / domyślne Orca
Template Custom G-code     puste
```

Ważne: nie dublować procedury `TOOLCHANGE_CLEAN` w dwóch różnych polach, jeśli Orca wykonuje oba. Należy sprawdzić wygenerowany G-code przy pierwszej realnej zmianie narzędzia.

---

## 8. Potwierdzone pola nagłówka classic `.zcode` Inventure

Potwierdzone / roboczo stabilne offsety nagłówka:

```text
50..53  bardzo mocny kandydat: licznik komend Z-Suite-like
54..57  czas druku
58..60  triplet trybu zadania / kompatybilności firmware
61      printer id
62      materiał modelowy
63      layer
64      quality
65      infill
66      support angle / parametr supportu
68..71  wersja Z-Suite / software version
73..74  długość filamentu modelowego
77..78  długość filamentu supportowego
85      materiał supportowy
127     CRC nagłówka
```

### 8.1. CRC

CRC nagłówka jest traktowane jako potwierdzone:

```text
byte 127 = CRC nagłówka
algorytm w konwerterze/patcherze jest poprawny
```

Jeśli drukarka zgłasza błąd materiałowy, pierwsze podejrzenia to zwykle:

```text
62
85
58..60
relacja model/support
```

a nie samo CRC.

### 8.2. Bajty 58..60

Bajty `58..60` nie są kodami materiałów. Zachowują się jak triplet trybu zadania / kompatybilności firmware.

Potwierdzone reguły:

```text
single-material                    -> 01 02 01
dual + BASF Ultrafuse BVOH         -> 01 02 01
dual + Z-SUPPORT                   -> 01 03 00
dual + Z-SUPPORT Plus              -> 01 03 00
dual + Z-SUPPORT Premium           -> 01 03 00
```

Praktyczna reguła:

```text
Z-SUPPORT family -> 01 03 00
BASF BVOH i single -> 01 02 01
```

### 8.3. Pole 50..53

Z oryginalnych `.zcode` Z-Suite wyszła mocna hipoteza:

```text
single: header[50..53] = liczba sparsowanych komend - 29
dual:   header[50..53] = liczba sparsowanych komend - 30
```

Przykłady z wcześniejszej analizy:

```text
bunnydecor single: header = komendy - 29
Silica dual:       header = komendy - 30
bunnydecor dual:   header = komendy - 30
```

Traktować jako silną hipotezę do implementacji / testów zgodności Z-Suite.

### 8.4. Byte 72

Wcześniejsze uproszczenie `single=7`, `dual=5` okazało się niepełne.

Obserwacje:

```text
single Z-PLA  -> byte72 = 7
single Z-FLEX -> byte72 = 0
dual Z-PLA + support / Z-SUPPORT family -> 4 albo 5
g2z.jar workflow -> często 6
```

Wniosek:

```text
byte72 nie jest prostą flagą single/dual.
Najlepiej traktować go jako klasę generatora/profilu i obsługiwać tabelarycznie albo przez opcję AUTO/manualną.
```

---

## 9. Mapowanie materiałów Zortrax i external

### 9.1. Materiały natywne Zortrax

```text
Z-ULTRAT           -> 0x01
Z-GLASS            -> 0x02
Z-HIPS             -> 0x03
Z-PCABS            -> 0x04
Z-PETG             -> 0x05
Z-ULTRAT PLUS      -> 0x06
Z-SUPPORT          -> 0x07
Z-ESD              -> 0x08
Z-PHA              -> 0x09
Z-PLA              -> 0x0A
Z-PLA PRO          -> 0x0B
Z-ASA PRO          -> 0x0C
Z-SUPPORT PLUS     -> 0x0D
Z-SEMIFLEX         -> 0x0E
Z-FLEX             -> 0x0F
Z-NYLON            -> 0x10
Z-SUPPORT PREMIUM  -> 0x11
Z-PEEK             -> 0x12
```

### 9.2. Materiały external/open

```text
ABS-BASED FILAMENT      -> 0x81
GLASS-TYPE FILAMENT     -> 0x84
FLEX-BASED FILAMENT     -> 0x85
PLA-BASED FILAMENT      -> 0x86
PETG-BASED FILAMENT     -> 0x87
NYLON-BASED FILAMENT    -> 0x89
ULTRAT-BASED FILAMENT   -> 0x91
ESD PETG-BASED FILAMENT -> 0x92
PLA PRO-BASED FILAMENT  -> 0x94
ASA PRO-BASED FILAMENT  -> 0x95
SEMIFLEX-BASED FILAMENT -> 0x96
```

### 9.3. BASF / BVOH

W logice `.zcode`/nagłówka projektu przyjęto:

```text
BASF ULTRAFUSE BVOH -> 0x17
```

Aliasy:

```text
BVOH
ULTRAFUSE BVOH
BASF BVOH
```

powinny mapować do `0x17`.

Uwaga: w analizie RFID `.mfd` pojawiał się też kod external `0x83` dla BASF Ultrafuse BVOH. Nie mieszać bezmyślnie mapowania RFID `.mfd` i mapowania nagłówka `.zcode`, bo to mogą być różne warstwy systemu.

---

## 10. Potwierdzone podstawowe komendy `.zcode`

### 10.1. Format komendy

W praktyce komendy mają postać:

```text
LEN OPCODE PAYLOAD CRC
```

Przykład komendy pozycji specjalnej:

```text
03 11 XX CRC
```

Wcześniejsze zapisy typu `03 11 09` były skrótem bez CRC. Pełna komenda ma 4 bajty.

### 10.2. HOME

```text
03 05 03 DD = HOME XY
03 05 04 89 = HOME Z
```

Do testów pozycji specjalnych zalecany był tylko `HOME XY`, bez `HOME Z`, bo home Z może zbliżyć głowicę do tacki i wypalać dziury.

### 10.3. Wybór narzędzia

```text
03 07 00 61 = select T0
03 07 01 B4 = select T1
```

### 10.4. Pozycje specjalne `03 11 XX`

Potwierdzone pełne komendy:

```text
03 11 00 EB
03 11 01 3E
03 11 02 94
03 11 03 41
03 11 04 15
03 11 05 C0
03 11 06 6A
03 11 07 BF
03 11 08 C2
03 11 09 17
03 11 0A BD
03 11 0B 68
```

Najważniejsze ustalenie praktyczne:

```text
03 11 09 17 = pozycja startowa / parkingowa T0
03 11 0A BD = pozycja startowa / parkingowa T1
```

Po testach potwierdzono, że miejsca wcześniej określane jako `drop` / `garbage` nie są pojemnikiem na odpady. Nie używać już tych nazw jako pewników fizycznych.

### 10.5. Center / kosz dla aktywnej głowicy

```text
03 11 00 EB = center / pozycja nad koszem dla aktywnej głowicy
```

Praktyczna obserwacja:

```text
Po wyborze aktywnej głowicy pozycja nad koszem jest centrowana dla tej głowicy.
Nieaktywna głowica jest wtedy trochę z boku.
```

Czyli `03 11 00` nie jest jedną absolutną pozycją carriage, tylko pozycją zależną od aktywnego T0/T1.

---

## 11. Moduły ruchów: switch, clean, purge

### 11.1. SWITCH_T0

Sekwencja z oryginalnych ZCode Z-Suite i testów:

```text
05 -> 0A -> 03 -> 01 -> select T0
```

Pełniej:

```text
06 02 20 1C 00 00 46   ; F7200
03 11 05 C0

06 02 20 1C 00 00 46   ; F7200
03 11 0A BD

06 02 20 1C 00 00 46   ; F7200
03 11 03 41

06 02 FA 00 00 00 25   ; F250
03 11 01 3E

03 07 00 61            ; select T0
```

### 11.2. SWITCH_T1

Sekwencja:

```text
06 -> 09 -> 04 -> 02 -> select T1
```

Pełniej:

```text
06 02 20 1C 00 00 46   ; F7200
03 11 06 6A

06 02 20 1C 00 00 46   ; F7200
03 11 09 17

06 02 20 1C 00 00 46   ; F7200
03 11 04 15

06 02 FA 00 00 00 25   ; F250
03 11 02 94

03 07 01 B4            ; select T1
```

### 11.3. CLEAN_PASS

Potwierdzony modułowy clean pass:

```text
CLEAN_PASS = 09 -> 07 -> 0A -> 08 -> 09 -> 07 -> 00
```

Warianty:

```text
SLOW_CLEAN_PASS = ten sam tor przy wolnym feedrate
FAST_CLEAN_PASS = ten sam tor przy szybkim feedrate
```

Potwierdzony test:

```text
SLOW_CLEAN_PASS x1 + FAST_CLEAN_PASS x3
```

działał bez homingu, bez purge i bez ręcznego wyboru narzędzia, jeśli aktywne narzędzie było właściwie ustawione.

Dla Z-Suite-like toolchange zidentyfikowano osobne tory:

```text
T1 clean path:
09 -> 07 -> 0A -> 08 -> 09 -> 07 -> 00

T0 clean path:
0A -> 08 -> 09 -> 07 -> 0A -> 08 -> 00
```

### 11.4. Purge aktywnej głowicy

Purge działa jako ruch E na aktualnie aktywnej głowicy.

Ogólny schemat:

```text
03 0A 08 37                  ; temporary relative E
06 02 ...                    ; feedrate purge
08 01 FF/EA/FE/FD 08 ...     ; ruch E
07 04 08 ...                 ; restore E
03 09 08 2A                  ; return absolute E, jeśli wymagane
```

Potwierdzony test purge 20 mm:

```text
03 0A 08 37
06 02 2C 01 00 00 DF
08 01 FF 08 00 4B 00 00 0D
07 04 08 00 00 00 00 C2
03 09 08 2A
```

Przelicznik:

```text
960 steps/mm
20 mm x 960 = 19200 steps = 0x4B00 = 00 4B 00 00
```

---

## 12. Procedura startowa DUAL z Z-Suite

Użytkownik potwierdził praktycznie fizyczną sekwencję:

```text
1. zjazd stołu do dolnego czujnika,
2. HOME XY,
3. pozycja nad koszem,
4. potwierdzenie opróżnienia kosza przyciskiem,
5. nagrzewanie ekstruderów,
6. ruch do zmiany T1,
7. powrót / center nad koszem,
8. stół idzie do góry od dolnego czujnika, ale nie jako HOME Z — zostaje ok. 5 mm od głowic,
9. HOME XY,
10. HOME Z,
11. stół w dół ok. 20 mm,
12. ruch do T1,
13. ruch nad kosz / center,
14. purge,
15. fast clean T1,
16. jeśli są dane druku -> start normalnego druku,
17. jeśli nie ma danych druku -> koniec.
```

Ważna interpretacja:

```text
Pierwsze kroki fizyczne — zjazd stołu, pierwszy HOME XY, kosz, potwierdzenie,
grzanie, pierwszy ruch do T1, center i podniesienie stołu do ok. 5 mm —
są efektem firmware’owego bloku startowego, a nie osobnych jawnych komend później.
```

### 12.1. FW_START_BASKET_CONFIRM_HEAT

Blok firmware’owy:

```text
03 0B 00 15
07 04 08 00 00 00 00 C2
08 01 FF 10 00 00 00 00 A7
06 0E ...
06 16 ...
07 08 ...
07 08 ...
02 14 BA
```

Praktycznie potwierdzono, że ten blok:

- opuszcza stół do dolnego czujnika,
- wykonuje procedurę kosza,
- wymaga potwierdzenia opróżnienia kosza,
- uruchamia nagrzewanie ekstruderów,
- realizuje część wstępnego pozycjonowania firmware.

Test 3x powtarzania tego bloku nie zadziałał jako trzy osobne procedury kosza. Firmware potraktował go jako wejście w jedną procedurę startową. Nie traktować `03 0B 00 15` / `02 14 BA` jako prostego, wielokrotnie wywoływalnego `EMPTY_BASKET_CONFIRM`.

### 12.2. Jawne HOME po firmware start

```text
03 05 03 DD = HOME XY
03 05 04 89 = HOME Z
```

### 12.3. BED/Z PREP

Powtarzalny blok po home:

```text
0F 04 07 00 00 00 00 00 00 00 00 00 00 00 00 C3
06 02 B4 00 00 00 FE
08 01 FF 04 FE 2E 00 00 30
06 1C 00 00 00 00 25
03 1A 01/02 ...
06 10 ...
03 1A 03 04
```

Semantyka pojedynczych komend nie jest jeszcze w pełni rozbita. Praktycznie to blok przygotowania stołu/Z po home.

### 12.4. SWITCH_T1_START

```text
06 -> 09 -> 04 -> 02 -> select T1
```

### 12.5. CENTER + E ruchy przed fast clean

Po `select T1`:

```text
03 11 00 EB
```

Potem dodatnie ruchy E. Przykład dla dual Z-PLA + Z-SUPPORT:

```text
08 01 EA 08 93 52 00 00 B0  ≈ 22.02 mm
08 01 FE 08 26 5A 00 00 CD  ≈ 24.04 mm
```

Użytkownik potwierdził dzięki pauzom 5 s, że te ruchy E fizycznie dzieją się przed fast clean. To realny purge/prime, nie neutralny blok przygotowawczy.

### 12.6. T1_FAST_CLEAN_PASS

```text
09 -> 07 -> 0A -> 08 -> 09 -> 07 -> 00
```

### 12.7. POST_CLEAN_E_MOVE

Po fast clean jest kolejny dodatni ruch E. Przykład:

```text
08 01 FD 08 A6 52 00 00 0D ≈ 22.04 mm
```

---

## 13. Procedura startowa SINGLE z Z-Suite

Potwierdzona praktycznie obserwacją oryginalnego pliku single Z-Suite:

```text
START SINGLE Z-Suite:
- procedura firmware start/kosz/grzanie,
- HOME XY,
- HOME Z,
- przygotowanie Z/stołu,
- przełączenie / ustawienie T0,
- center nad koszem dla T0,
- purge / prime T0,
- brak jawnego fast clean path,
- start druku.
```

Ważny wniosek:

```text
START_MACHINE SINGLE ≠ START_MACHINE DUAL z podstawieniem T0.
```

W single występuje:

```text
SWITCH_T0_START = 05 -> 0A -> 03 -> 01 -> select T0
CENTER = 00
E ruchy purge/prime T0
brak jawnego fast clean path
```

---

## 14. Profile purge/prime i retrakcja

### 14.1. Profile startowych E ruchów

Konwerter dobiera długości E po materiałach rozpoznanych z G-code / ORCA METADATA.

SINGLE:

```text
Z-FLEX: 20.00 / 22.50 / 20.00 mm
Z-PLA:  20.00 / 21.00 / 20.00 mm
fallback średni: 20.00 / 21.75 / 20.00 mm
```

DUAL:

```text
Z-PLA + Z-SUPPORT:                  22.02 / 24.04 / 22.04 mm
Z-GLASS + Z-SUPPORT Premium:        22.52 / 25.04 / 22.54 mm
Z-SEMIFLEX + Z-SUPPORT Premium:     22.02 / 24.04 / 22.04 mm
Z-ULTRAT Plus + Z-SUPPORT Premium:  21.00 / 22.00 / 21.00 mm
ABS-based + Z-SUPPORT Premium:      21.00 / 22.00 / 21.00 mm
fallback średni:                    21.85 / 23.69 / 21.86 mm
```

Wniosek:

```text
Nie wpisywać jednej stałej purge dla wszystkich materiałów.
Używać profilu materiałowego albo fallbacku średniego.
```

### 14.2. Retrakcja starej głowicy przy toolchange

Analiza oryginalnych duali Z-Suite wskazała praktycznie stałą retrakcję starej głowicy:

```text
-20.00 mm przy F480
```

T0 przed przejściem na T1:

```text
06 02 E0 01 00 00 D5       ; F480
08 01 E9 08 00 B5 FF FF CB ; -20.00 mm
```

T1 przed przejściem na T0:

```text
06 02 E0 01 00 00 D5       ; F480
08 01 F3 08 00 B5 FF FF 6C ; -20.00 mm
```

Do konwertera:

```text
IDLE_RETRACT=AUTO = -20 mm @ F480
```

W v1.2.7 można spowolnić F480 przez:

```gcode
RETRACT_SPEED_SCALE=0.5
```

Jeśli filament nadal się urywa, testować ręcznie:

```gcode
IDLE_RETRACT=10
```

---

## 15. TOOLCHANGE_CLEAN — aktualna logika

Przy `TOOLCHANGE_CLEAN` wykonywane jest:

```text
1. preheat nowej głowicy do temperatury z Orca,
2. Z-Suite-like switch path,
3. retrakcja starej głowicy -20 mm @ F480, skalowalna przez RETRACT_SPEED_SCALE,
4. po retrakcji obniżenie temperatury starej / nieaktywnej głowicy,
5. wait temperatury nowej głowicy,
6. purge/prime wg profilu materiałowego, skalowalne przez E_SPEED_SCALE,
7. clean path T0/T1,
8. post-clean E move / restore.
```

Dla T1:

```text
06 -> 09 -> retract old -> 04 -> 02 -> select T1
00
E1 / E2
09 -> 07 -> 0A -> 08 -> 09 -> 07 -> 00
E3 / restore
```

Dla T0:

```text
05 -> 0A -> retract old -> 03 -> 01 -> select T0
00
E1 / E2
0A -> 08 -> 09 -> 07 -> 0A -> 08 -> 00
E3 / restore
```

`TOOLCHANGE_CLEAN` robi własny purge/prime przy realnej zmianie narzędzia. To jest potrzebne, ale dlatego `LAYER_CLEAN` w v1.2.6+ ma `SKIP_AFTER_TOOLCHANGE=1`, aby nie robić drugiego purge zaraz po toolchange.

---

## 16. LAYER_CLEAN — aktualna logika

Zalecany wpis v1.2.7:

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

Cele zmian v1.2.5 i v1.2.6:

```text
START_LAYER=2:
- nie rób layer clean na pierwszej drukowanej warstwie,
- nie dubluj purge zaraz po START_MACHINE.

SKIP_AFTER_TOOLCHANGE=1:
- nie rób layer clean na tej samej warstwie bezpośrednio po TOOLCHANGE_CLEAN.
```

`LAYER_CLEAN` w zalecanym układzie nie robi osobnej retrakcji starej głowicy, bo działa na aktualnie aktywnej głowicy.

---

## 17. Temperatury i ooze prevention

### 17.1. START_MACHINE

W v1.2.3+ po firmware’owym nagrzewaniu i przed purge/prime `START_MACHINE` wymusza temperaturę z Orca. To było ważne, bo np. firmware’owy profil mógł mieć `90°C`, co jest za mało dla ABS.

### 17.2. TOOLCHANGE_CLEAN

Przywrócono ooze prevention:

```text
preheat nowej głowicy,
retract starej -20 mm,
po retrakcji obniż temperaturę nieaktywnej głowicy,
wait nowej głowicy,
purge/clean.
```

Standby dla starej głowicy:

```text
idle_temperature_tN jeśli > 0
albo standby_temperature_delta z Orca
albo fallback -20°C względem temperatury materiału
```

### 17.3. PREHEAT_TIME=AUTO

W v1.2.4 poprawiono interpretację:

```text
PREHEAT_TIME=AUTO bierze preheat_time z ORCA METADATA,
np. 8 s,
a nie pokazuje już błędnie -1 s.
```

---

## 18. Placeholdery ORCA METADATA — co jest wykorzystywane

Konwerter wczytuje cały blok ORCA METADATA do słownika. Aktywnie używane pola:

```text
process
layer_height
filament_t0 / filament_type_t0
filament_t1 / filament_type_t1
support_material / support_material_type
support
support_threshold_angle
infill_density
nozzle_temperature_t0/t1
nozzle_temperature_initial_layer_t0/t1
idle_temperature_t0/t1
standby_temperature_delta
ooze_prevention
preheat_time
retraction_speed_t0/t1
deretraction_speed_t0/t1
travel_speed
curr_bed_type + bed_temp_* — parsowane / rezerwowe
```

Z `ZORTRAX_TOOLCHANGE_META` dynamicznie używane:

```text
previous_extruder
next_extruder
old_temp
new_temp
layer_num
flush_length / dane flush jako źródła pomocnicze przy AUTO
```

Rezerwowe / przyszłościowe:

```text
mode
initial_layer_print_height
travel_speed_z
support_speed
support_interface_speed
retraction_length_t0/t1
retract_restart_extra_t0/t1
retract_length_toolchange_t0/t1
retract_restart_extra_toolchange_t0/t1
chamber_temperature_t0/t1
top_layers
bottom_layers
support_type
```

---

## 19. OpCode 0x1A, 0x15, 0x12

### 19.1. Opcode 0x1A

Format:

```text
03 1A XX CRC
```

Interpretacja robocza:

```text
marker stanu / fazy firmware / procedury,
nie ruch XY/Z i nie purge.
```

Zaobserwowane:

```text
03 1A 01
03 1A 02
03 1A 03
03 1A 04
03 1A 65
03 1A 66
03 1A 67
03 1A 68
```

Najlepiej potwierdzone:

```text
03 1A 01/02 występuje w BED/Z PREP
03 1A 03 domyka/przełącza część BED/Z PREP
03 1A 67 występuje przy końcu startu, przed 03 15 03
```

### 19.2. Opcode 0x15

Format:

```text
03 15 XX CRC
```

Najważniejszy kontekst:

```text
03 1A 67 C3
03 15 03 6D
```

Interpretacja:

```text
marker przejścia po procedurze startowej do normalnego druku.
```

`03 15 00` występuje później jako marker fazy/stanu, nie ruch.

### 19.3. Opcode 0x12

Ważne: `opcode 0x12` w strumieniu komend to nie to samo co materiał `0x12 = Z-PEEK`.

`0x12` pojawia się jako duże końcowe bloki:

```text
FF 12 ...
```

Interpretacja po analizach:

```text
sekcja danych pomocniczych / preview / obraz hotbed,
nie ruch i nie procedura mechaniczna.
```

---

## 20. Reverse engineering preview `opcode 0x12`

Użytkownik potwierdził, że to preview zależne od wyglądu modelu na hotbed.

Analiza wykazała:

- końcowe bloki `opcode 0x12` tworzą sklejony blob,
- struktura segmentu wygląda jak:

```text
u32_le declared_size
u32_le 256
u16 zmienne
body danych
footer 23–24 bajty
```

Przykładowe wyniki:

```text
bunnydecor single: 1 segment, body ok. 7324 B
bunnydecor dual:   1 segment, body ok. 7340 B
Silica dual:       1 segment, body ok. 7356 B
gasket single:     3 segmenty, body ok. 7324 B każdy
hero/support:      2 segmenty, body ok. 7356 B każdy
```

Wygenerowano:

```text
zortrax_preview_extraction_package.zip
extract_zortrax_preview_blocks.py
zortrax_preview_extraction/README_preview_extraction_PL.md
zortrax_preview_extraction/preview_segments_summary.csv
zortrax_preview_extraction/all_candidate_images_contact_sheet.png
```

Wniosek:

```text
0x12 to praktycznie na pewno preview / hotbed image,
ale format nie jest jeszcze w pełni zdekodowany.
Nie jest to PNG/JPEG/BMP wprost.
Najpewniej jest zakodowany / skompresowany / obfuskowany raster lub dane podglądu.
```

Do konwertera:

```text
0x12 nie jest wymagany do ruchu drukarki.
Można go pominąć dla funkcjonalnego druku.
Dla pełnej zgodności z Z-Suite trzeba kiedyś odtworzyć/generować preview.
```

---

## 21. Potwierdzone testy praktyczne

### 21.1. Testy modułów

Potwierdzone:

```text
zortrax_nohome_purge20mm_current_tool_F300.zcode
```

Sam purge 20 mm działa poprawnie.

Potwierdzone:

```text
zortrax_nohome_clean_slow1_fast3_current_path.zcode
```

`SLOW_CLEAN_PASS x1 + FAST_CLEAN_PASS x3` działa poprawnie.

Potwierdzone:

```text
zortrax_T1_split_sequences_homeXY_only_purge6.zcode
```

Rozbicie sekwencji T1 z separatorami HOME XY działało zgodnie z procedurą.

### 21.2. Testy v1.2.2

Potwierdzone poprawne wykonanie:

```text
test_dual_zpla_zsupport_auto_toolchange_layer_v122.zcode
test_single_zpla_auto_layer_v122.zcode
```

Wnioski:

```text
AUTO purge po materiale działa.
IDLE_RETRACT=AUTO = -20 mm działa.
toolchange clean dual działa.
layer clean co N warstw działa.
single layer clean działa.
```

### 21.3. v1.2.3 / v1.2.4

```text
v1.2.3 dodała temperatury z Orca przed purge i ooze prevention.
v1.2.4 poprawiła log/progress i PREHEAT_TIME=AUTO.
```

### 21.4. v1.2.5 / v1.2.6

```text
v1.2.5: START_LAYER=2 rozwiązuje problem layer clean na pierwszej warstwie po startowym purge.
v1.2.6: SKIP_AFTER_TOOLCHANGE=1 rozwiązuje problem dodatkowego layer clean po toolchange clean.
```

### 21.5. v1.2.7

```text
v1.2.7: E_SPEED_SCALE=0.5 i RETRACT_SPEED_SCALE=0.5 dodane dla START_MACHINE, TOOLCHANGE_CLEAN, LAYER_CLEAN i START_PURGE.
Użytkownik: wygląda, że działa OK.
```

---

## 22. Rzeczy, których nie robić / pułapki

Nie używać już starych nazw jako fizycznie pewnych:

```text
GarbageCenter
GarbageOutside
Drop
```

Nie traktować:

```text
03 11 09
03 11 0A
```

jako kosza. To pozycje startowe/parkingowe T0/T1.

Nie dodawać `HOME Z` do testów pozycji specjalnych, jeśli celem nie jest procedura startowa — może zbliżyć głowicę do tacki.

Nie dodawać:

```gcode
;ZORTRAX_START_PURGE
```

po:

```gcode
;ZORTRAX_START_MACHINE
```

w v1.2.3+ — start machine ma już własny purge/prime.

Nie używać starego:

```gcode
;ZORTRAX_SPECIAL_CLEAN AUTO 5 ...
```

jako głównej procedury toolchange/layer. Zastąpione jest przez:

```gcode
;ZORTRAX_TOOLCHANGE_CLEAN ...
;ZORTRAX_LAYER_CLEAN ...
```

Nie dublować `TOOLCHANGE_CLEAN` w dwóch polach Orca.

Nie wyciągać wniosków z porównania nieekwiwalentnych plików `.zcode`.

---

## 23. Homing i kalibracja

### 23.1. Homing

Potwierdzone:

```text
03 05 03 DD = HOME XY
03 05 04 89 = HOME Z
```

Problem wcześniejszej wersji:

```text
G28 bez parametrów generował 03 05 7F 61
```

To nie jest preferowany układ Z-Suite. Zalecane mapowanie gołego `G28`:

```text
03 05 03 DD
03 05 04 89
```

czyli osobno HOME XY i HOME Z.

### 23.2. Nozzle Alignment / Platform Leveling

Nie znaleziono potwierdzonej komendy G-code / `.zcode`, która uruchamia firmware’owe:

```text
Maintenance -> Nozzle Alignment Calibration
Maintenance -> Platform Leveling
```

To są procedury interaktywne z menu drukarki. Można zrobić własny testowy wzorzec kontrolny, ale nie zapisze on offsetu w firmware.

---

## 24. Workflow i launchery

Aktualny kierunek projektu:

```text
pure Python converter
bez aktywnego g2z.jar w głównym workflow
bez starego C:\OrcaScripts\out fallback dla Orca .gcode.pp
```

Dla Orca `.gcode.pp` output powinien pochodzić ze zmiennych środowiskowych Orca, np. `SLIC3R_PP_OUTPUT_NAME`.

Windows:

- prosty `.bat`, unikać PowerShell/Tee,
- progress czytelny,
- Unicode-safe fallback.

macOS:

- może działać cicho w tle,
- log wystarczy,
- nie wymuszać Terminal.app, chyba że użytkownik wyraźnie poprosi.

---

## 25. Orca bundle / presety — najważniejsze zasady

Preferowany finalny układ Orca:

```text
1 bundle .orca_printer
2 drukarki:
- Zortrax Inventure 0.4 nozzle - single
- Zortrax Inventure 0.4 nozzle - dual
8 processów:
- 4 single
- 4 dual
wspólne filamenty
```

Domyślne presety:

```text
Dual:
default_print_profile = 0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual
default_filament_profile = [Z-PLA, Z-SUPPORT]

Single:
default_print_profile = 0.15mm Quality @Zortrax Inventure 0.4 nozzle - single
default_filament_profile = [Z-PLA]
```

Przy pracy na `.orca_printer`:

- traktować jako ZIP,
- utrzymywać poprawność JSON,
- aktualizować `bundle_structure.json`,
- nie zostawiać osieroconych referencji,
- przy zmianie nazwy aktualizować `name`, `*_settings_id`, nazwę pliku i referencje,
- przy scalaniu presetów nie kopiować pól tożsamości (`name`, `inherits`, `print_settings_id`).

---

## 26. RFID `.mfd` — najważniejsze poboczne ustalenia

Plik `.mfd` traktowany jest jako dump MIFARE Classic 1K:

```text
16 sektorów
4 bloki po 16 bajtów
1024 bajty
```

Najważniejsze bloki:

```text
Sector 1 / block 4 — identyfikacja materiału i nominalny raw
Sector 1 / block 5 — nazwa koloru/materiału ASCII
Sector 1 / block 6 — CRC sektora
Sector 2 / block 8 — aktualna ilość materiału raw
Sector 2 / block 10 — CRC sektora
```

CRC RFID:

```text
CRC8_DVB_S2
poly = 0xD5
init = 0x00
bez final xor
bez odbicia bitów
```

Ustalono m.in. `0x80 = External` w firmware RFID Inventure, ale nie mieszać bezpośrednio z mapowaniem nagłówka `.zcode`.

---

## 27. Otwarte tematy

Nadal otwarte / do dalszego reverse engineeringu:

1. Pełne znaczenie wszystkich nieudokumentowanych pól nagłówka poza potwierdzonymi.
2. Pełna tabela `byte72` dla wszystkich profili / materiałów / workflow.
3. Ostateczne zdekodowanie preview `opcode 0x12`.
4. Pełne znaczenie `0x1A` i `0x15` w późniejszych fazach druku.
5. Dalsze profile purge/prime dla większej liczby materiałów.
6. Ewentualne `PURGE_TOTAL_DELTA`, `PURGE_EACH_DELTA`, `IDLE_RETRACT_DELTA` w przyszłej wersji, jeśli samo spowolnienie E nie wystarczy.
7. Pełna zgodność strumienia komend pure Python z oryginalnym Z-Suite.
8. Firmware update — payload pozostaje zaszyfrowany/nieodczytany.

---

## 28. Najkrótszy prompt startowy do nowego chatu

Można wkleić do nowego chatu:

```text
Kontynuujemy projekt Zortrax Inventure / Orca.

Aktualna wersja konwertera: v1.2.7-e-speed-scale.

Najważniejsze:
- aktywny workflow to pure Python .zcode converter,
- aktualne markery: START_MACHINE, TOOLCHANGE_CLEAN, LAYER_CLEAN, END_MACHINE,
- v1.2.7 dodaje E_SPEED_SCALE= i RETRACT_SPEED_SCALE= dla START_MACHINE, TOOLCHANGE_CLEAN, LAYER_CLEAN i START_PURGE,
- dla kruchego PVA/BVOH/Z-SUPPORT zalecane: E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5,
- START_MACHINE zawiera już startowy purge/prime, nie dodawać po nim START_PURGE,
- TOOLCHANGE_CLEAN robi purge/prime przy realnej zmianie T0/T1,
- LAYER_CLEAN ma START_LAYER=2 i SKIP_AFTER_TOOLCHANGE=1,
- potwierdzone HOME: 03 05 03 DD = XY, 03 05 04 89 = Z,
- select: 03 07 00 61 = T0, 03 07 01 B4 = T1,
- 03 11 09 = parking/start T0, 03 11 0A = parking/start T1,
- 03 11 00 = center nad koszem dla aktywnej głowicy,
- clean T1: 09 -> 07 -> 0A -> 08 -> 09 -> 07 -> 00,
- clean T0: 0A -> 08 -> 09 -> 07 -> 0A -> 08 -> 00,
- IDLE_RETRACT=AUTO = -20 mm @ F480, a v1.2.7 może skalować prędkość przez RETRACT_SPEED_SCALE,
- potwierdzone pola nagłówka: 54..57, 58..60, 61, 62, 63, 64, 65, 66, 68..71, 73..74, 77..78, 85, 127,
- 58..60: single i BASF BVOH -> 01 02 01, Z-SUPPORT family -> 01 03 00,
- opcode 0x12 to preview/hotbed image, nie ruch,
- nie używać starych nazw drop/garbage jako pewników fizycznych.
```

---

## 29. Minimalny stan końcowy

Najbezpieczniejszy aktualny zestaw dla v1.2.7:

DUAL:

```gcode
;ZORTRAX_START_MACHINE DUAL E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5

M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400

G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO

;ZORTRAX_END_MACHINE AUTO
```

SINGLE:

```gcode
;ZORTRAX_START_MACHINE SINGLE E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5

Change filament / Tool change: puste

G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO

;ZORTRAX_END_MACHINE AUTO
```

Dla normalnych materiałów można usunąć `E_SPEED_SCALE` / `RETRACT_SPEED_SCALE` albo ustawić `1.0`.


## A19. `ZORTRAX_INVENTURE_kontekst_transfer_full.md`

# ZORTRAX INVENTURE — pełny kontekst roboczy do przeniesienia do nowego chatu

Ten plik ma przenieść **cały istotny stan prac** nad:
- presetami **OrcaSlicer** dla **Zortrax Inventure 0.4 nozzle**,
- konwersją `G-code -> Z-code` przez `g2z.jar`,
- patchowaniem nagłówka `.zcode` dla Inventure,
- analizą firmware update dla Inventure,
- rozdzieleniem presetów `single` / `dual` i testami zgodności.

Celem tego pliku jest umożliwienie kontynuowania pracy w nowym chacie **bez odtwarzania kontekstu od zera**.

---

## 1. Najważniejszy stan projektu

Aktualnie ustalone i potwierdzone są cztery główne obszary pracy:

1. **Patcher `.zcode` dla Inventure**
   - aktywnie używana linia rozwojowa patchera to wersja oparta o `g2z_hybrid_wrapper_v10_orca_outdir_named.py`
   - rozwinięta i przetestowana wersja to: `g2z_hybrid_wrapper_v10_orca_outdir_named_UPDATED.py`
   - patcher czyta metadane z G-code z Orca i nadpisuje potwierdzone pola nagłówka `.zcode`

2. **Bundle OrcaSlicer dla Inventure**
   - finalny, wygodny wariant to **jeden bundle** `.orca_printer` zawierający:
     - **2 drukarki**: `single` i `dual`
     - **4 processy single**
     - **4 processy dual**
     - **wspólne filamenty**

3. **Mapowanie materiałów i trybów supportu**
   - potwierdzono kody materiałów i logikę pól nagłówka dla supportów Zortrax i BASF BVOH

4. **Firmware update Inventure**
   - update firmware został rozpoznany jako vendorowy kontener z jednym wysokorandomowym payloadem
   - nie udało się jeszcze wydobyć z niego komend ani map materiałów

---

## 2. Potwierdzone pola nagłówka classic `.zcode` dla Inventure

To są pola, które należy traktować jako potwierdzone roboczo dla classic ZCode Inventure:

- `54..57` — czas druku
- `61` — printer id
- `62` — materiał modelowy
- `63` — layer
- `64` — quality
- `65` — infill
- `66` — support angle / pole wykorzystywane przez Z-Suite jako parametr supportu
- `68..71` — wersja Z-Suite / software version
- `73..74` — długość filamentu modelowego
- `77..78` — długość filamentu supportowego
- `85` — materiał supportowy
- `127` — CRC nagłówka

Dodatkowo praktycznie potwierdzono znaczenie:
- `58..60` — **triplet trybu kompatybilności / firmware / konfiguracji zadania**

---

## 3. Najważniejsze ustalenie o bajtach 58–60

Najpierw była hipoteza, że 58–60 odnoszą się bezpośrednio do materiałów lub dual/single. Ostateczne ustalenie jest takie:

- **58–60 nie są kodami materiałów**
- są traktowane jak **triplet trybu kompatybilności / profilu zadania / minimalnego trybu firmware**
- w praktyce dla Inventure sterują rozpoznaniem trybu supportu

Potwierdzona logika robocza:

- **single-material** → `01 02 01`
- **dual + BASF Ultrafuse BVOH** → `01 02 01`
- **dual + Z-SUPPORT** → `01 03 00`
- **dual + Z-SUPPORT Plus** → `01 03 00`
- **dual + Z-SUPPORT Premium** → `01 03 00`

Wniosek praktyczny:
- rodzina **Z-SUPPORT / Plus / Premium** używa trybu `01 03 00`
- **BASF BVOH** i single używają `01 02 01`

---

## 4. Potwierdzone mapowanie materiałów w patcherze

### Natywne materiały Zortrax

- `Z-ULTRAT` → `0x01`
- `Z-GLASS` → `0x02`
- `Z-HIPS` → `0x03`
- `Z-PCABS` → `0x04`
- `Z-PETG` → `0x05`
- `Z-ULTRAT PLUS` → `0x06`
- `Z-SUPPORT` → `0x07`
- `Z-ESD` → `0x08`
- `Z-PHA` → `0x09`
- `Z-PLA` → `0x0A`
- `Z-PLA PRO` → `0x0B`
- `Z-ASA PRO` → `0x0C`
- `Z-SUPPORT PLUS` → `0x0D`
- `Z-SEMIFLEX` → `0x0E`
- `Z-FLEX` → `0x0F`
- `Z-NYLON` → `0x10`
- `Z-SUPPORT PREMIUM` → `0x11`
- `Z-PEEK` → `0x12`

### Materiały external / open

- `ABS-BASED FILAMENT` → `0x81`
- `GLASS-TYPE FILAMENT` → `0x84`
- `FLEX-BASED FILAMENT` → `0x85`
- `PLA-BASED FILAMENT` → `0x86`
- `PETG-BASED FILAMENT` → `0x87`
- `NYLON-BASED FILAMENT` → `0x89`
- `ULTRAT-BASED FILAMENT` → `0x91`
- `ESD PETG-BASED FILAMENT` → `0x92`
- `PLA PRO-BASED FILAMENT` → `0x94`
- `ASA PRO-BASED FILAMENT` → `0x95`
- `SEMIFLEX-BASED FILAMENT` → `0x96`

### BASF support

Najważniejsze robocze ustalenie:
- `BASF Ultrafuse BVOH` → **`0x17`**

To jest bardzo ważne, bo wcześniej była błędna/nieaktualna wersja mapowania, gdzie BASF BVOH występował inaczej. W aktywnej logice patchera dla Inventure należy trzymać:
- `BASF ULTRAFUSE BVOH` → `0x17`
- aliasy typu `BVOH`, `ULTRAFUSE BVOH`, `BASF BVOH` też powinny mapować do `0x17`

---

## 5. Kluczowe ustalenie o CRC

Było sprawdzane wielokrotnie i należy to traktować jako **potwierdzone**:

- algorytm CRC używany w patcherze jest poprawny
- CRC w bajcie `127` jest liczone prawidłowo
- CRC zgadza się z referencyjnymi plikami `.zcode` z Z-Suite

Wniosek:
- jeśli drukarka zgłasza błąd materiału, **to nie wygląda na problem CRC**, tylko raczej na niezgodność któregoś pola nagłówka, najczęściej materiału lub relacji materiałów

---

## 6. Logika patchera — aktywna, przetestowana wersja

Docelowa logika patchera dla Inventure:

1. czyta G-code z Orca
2. czyta blok `ORCA METADATA`
3. wyciąga z niego m.in.:
   - `process`
   - `layer_height`
   - `filament_t0`
   - `filament_t1`
   - `support`
   - `support_type`
   - `support_threshold_angle`
   - `infill_density`
   - `top_layers`
   - `bottom_layers`
4. czyta też fallbacki z komentarzy typu:
   - `; filament used [mm] = ...`
   - `; filament_type = ...`
   - `; filament_settings_id = ...`
5. ustala:
   - `model_code`
   - `support_code`
   - `single_material`
   - `support_length_mm`
   - `model_length_mm`
6. ustala `fw_triplet` wg reguły supportu
7. patchuje nagłówek `.zcode`
8. przelicza CRC

### Reguła single-material

Patcher powinien traktować plik jako single, jeśli:
- `support_length_mm == 0`
- albo support code jest pusty / równy modelowi i nie ma realnego zużycia supportu

W single:
- `support_code` ma zostać ustawiony na `model_code`
- `support_length_mm = 0`
- `58..60 = 01 02 01`

### Reguła fw_triplet

Dla aktywnej wersji patchera należy używać logiki:

- jeśli support realnie występuje i `support_code` należy do rodziny Z-SUPPORT (`0x07`, `0x0D`, `0x11`) → `01 03 00`
- we wszystkich pozostałych przypadkach → `01 02 01`

---

## 7. Wyniki testów patchera — potwierdzone

### Testy single

Potwierdzone działanie dla single:
- `58–60 = 01 02 01`
- `85 = model_code`
- CRC poprawne

### Testy dual + BASF BVOH

Potwierdzone działanie:
- `58–60 = 01 02 01`
- `62 = model material`
- `85 = 0x17`

### Testy dual + Z-SUPPORT family

Potwierdzone działanie:
- `Z-SUPPORT` → `85 = 0x07`, `58–60 = 01 03 00`
- `Z-SUPPORT Plus` → `85 = 0x0D`, `58–60 = 01 03 00`
- `Z-SUPPORT Premium` → `85 = 0x11`, `58–60 = 01 03 00`

### Test 1-stopniowy i 2-stopniowy

Były testowane dwa workflow:

#### A. 1-stopniowy
`gcode -> g2z.jar -> patcher`

Finalnie uznano, że:
- działa poprawnie dla testów `single`, `dual + BASF`, `dual + Z-SUPPORT family`

#### B. 2-stopniowy
1. `java -jar g2z.jar ...`
2. `python patcher.py --no-run-jar ...`

To także działa poprawnie i jest bezpiecznym workflow diagnostycznym.

---

## 8. Bardzo ważne zastrzeżenie metodologiczne

Był moment, kiedy wyciągnięto zły wniosek z porównania **nieekwiwalentnych plików**:
- patched `.zcode` z Orca dla jednego modelu
- oryginalny `.zcode` z Z-Suite dla innego modelu / innych ustawień

Ten wniosek należy uznać za **odrzucony**.

Nie wolno już przyjmować bez ścisłego porównania, że problem powoduje np.:
- `66`
- `support_threshold_angle`
- albo inne pole, jeśli porównywane pliki nie dotyczą tego samego modelu i podobnych ustawień.

Poprawna metoda porównania:
- ten sam model
- możliwie ten sam profil
- Orca G-code
- wynik `g2z.jar`
- wynik `g2z.jar + patch`
- referencyjny `.zcode` z Z-Suite

Dopiero takie porównanie daje wiarygodne wnioski.

---

## 9. Ustalenia dotyczące firmware update Inventure

Do projektu zostały wgrane różne wersje firmware update dla Inventure.

### Rozpoznana struktura pliku update

Każdy `InventureUpdate.bin` ma format:

- `0x00..0x03` → `ZRTX`
- `0x04..0x07` → `UINV`
- `0x08..0x0C` → `rNNNN`
- `0x0D..0x10` → stałe pole `225`
- `0x11..0x14` → długość payloadu
- `0x15..EOF` → jeden payload

### Rozpoznane rewizje

- `r0155` → 1.2.0
- `r0207` → 1.2.1
- `r0219` → 1.2.2
- `r0232` → 1.3.1
- `r0279` → 1.4.0
- `r0300` → 1.5.1
- `r0309` → 1.5.4
- `r0323` → 1.6.1

### Najważniejszy wniosek o payloadzie

Payload:
- ma bardzo wysoką entropię
- jest podzielny przez 16
- nie zawiera jawnych stringów
- nie wygląda jak ZIP/gzip/LZMA/ELF
- nie ma powtarzających się bloków 16 B / 32 B

Najbardziej prawdopodobny model:
- payload jest szyfrowany albo opakowany w sposób dający efekt szyfrowania
- bardzo możliwy układ:
  - 16 B nagłówka kryptograficznego / IV / nonce
  - ciphertext
  - 16 B tag/MAC

### Wniosek praktyczny

Z plików firmware update **nie udało się jeszcze bezpośrednio wydobyć**:
- komend drukarki
- map materiałów
- dodatkowych offsetów do patchera

To trzeba traktować jako **nierozwiązane**.

---

## 10. Praca na `.orca_printer` — najważniejsze ustalenia

### Ogólna struktura bundla

W finalnej logice projektu wygodny wariant to:
- **1 bundle `.orca_printer`**
- **2 presety drukarki**
  - `Zortrax Inventure 0.4 nozzle - single`
  - `Zortrax Inventure 0.4 nozzle - dual`
- **8 processów**
  - 4 tylko dla `single`
  - 4 tylko dla `dual`
- **wspólne filamenty**

### Kluczowe zasady spójności

Przy każdej zmianie trzeba pilnować:
- poprawności ZIP
- poprawności JSON
- zgodności z `bundle_structure.json`
- braku osieroconych referencji
- spójności pól:
  - `name`
  - `*_settings_id`
  - nazwa pliku JSON
  - wpisy w `bundle_structure.json`
  - `compatible_printers`

### Zmiany nazw presetów

Przy zmianie nazwy presetu trzeba zmieniać jednocześnie:
- `name`
- `printer_settings_id` / `print_settings_id` / `filament_settings_id`
- nazwę pliku presetowego
- wpis w `bundle_structure.json`
- wszelkie referencje w `compatible_printers`

### Scalanie procesów

Przy scalaniu presetów **nie kopiować pól tożsamości**:
- `name`
- `inherits`
- `print_settings_id`

Kopiować tylko pola technologiczne.

---

## 11. Ustalenie dotyczące problemu eksportu process preset w Orca

Sprawdzony bundle nie był uszkodzony jako ZIP ani JSON.

Roboczy wniosek:
- problem z eksportem process preset wynikał raczej z zachowania/ograniczenia Orca 2.3.x niż z uszkodzenia bundla

Praktyczna reguła:
- jeśli eksport procesu nie działa, najpierw importować bundle, potem zrobić `Save As` procesu w Orca, a dopiero potem próbować eksportu.

---

## 12. Ustalenie o `0.08mm Ultra Quality`

Dodawany był proces:
- `0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle`

Najważniejsze założenia:
- proces jakościowy, bezpieczny
- bazowany na `0.15mm Quality`
- z obniżonymi prędkościami i akceleracjami
- wymagał obniżenia `min_layer_height` w presecie drukarki z `0.15` do `0.08`

Dla wariantu single, jeśli proces 0.08 jest kopiowany z dual, trzeba dopilnować:
- `support_filament = 0`
- `support_interface_filament = 0`

bo wartości z dual nie są poprawne dla single.

---

## 13. Finalne domyślne presety dla single i dual

W finalnych bundle ustawiono następujące wartości domyślne.

### Dual
- `default_print_profile = "0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual"`
- `default_filament_profile = ["Z-PLA", "Z-SUPPORT"]`

### Single
- `default_print_profile = "0.15mm Quality @Zortrax Inventure 0.4 nozzle - single"`
- `default_filament_profile = ["Z-PLA"]`

To ma zostać zachowane jako finalny stan.

---

## 14. User presets vs system presets

Było analizowane, czy bundle da się zrobić tak, aby preset pojawiał się w Orca jako **System Presets**, a nie **User Presets**.

Najuczciwszy wniosek:
- **sam importowany `.orca_printer` pozostaje bundlem użytkownika**
- nie należy zakładać, że samą zmianą JSON uda się go wiarygodnie przenieść do system presets

Aktualna decyzja projektowa:
- **pozostawić bundle jako user preset**
- tylko dopracować domyślne processy i filamenty

---

## 15. Najważniejsze wygenerowane pliki i artefakty

W rozmowie powstały m.in.:

- różne wersje `.orca_printer` dla single, dual i wspólnego bundla
- `g2z_hybrid_wrapper_v10_orca_outdir_named_UPDATED.py`
- ZIP z nową wersją patchera
- pliki testowe `.zcode` dla single i dual
- plik `.md` z reverse engineeringiem firmware
- pliki inwentaryzacji i snapshoty ZIP

Najważniejsze roboczo na końcu były:
- aktywny patcher `...UPDATED.py`
- finalne presety `single` i `dual`
- wspólny bundle: 2 drukarki + 8 processów + wspólne filamenty

---

## 16. Co jest potwierdzone, a co nadal otwarte

### Potwierdzone

- CRC nagłówka
- znaczenie podstawowych offsetów nagłówka
- logika `58..60`
- mapowanie BASF BVOH na `0x17`
- logika Z-SUPPORT family → `01 03 00`
- poprawność 1-stopniowego i 2-stopniowego patchowania w testach
- poprawność strukturalna finalnych bundle dla Orca

### Otwarte / nierozwiązane

- pełne znaczenie wszystkich nieudokumentowanych bajtów nagłówka poza potwierdzonymi polami
- pełne znaczenie pola stałego `225` w firmware update
- rozpakowanie/odszyfrowanie payloadu firmware
- pełna lista nieznanych komend firmware Inventure
- przypadki, w których drukarka zgłasza „nieprawidłowy materiał modelowy” mimo poprawnego CRC — to wymaga ścisłego porównania ekwiwalentnych plików

---

## 17. Najważniejsze reguły na dalszą pracę

1. Nie wyciągać wniosków z porównań nieekwiwalentnych plików.
2. Przy analizie materiałów skupiać się najpierw na:
   - `62`
   - `85`
   - `58..60`
   - CRC
3. Przy pracy na `.orca_printer` zawsze utrzymywać spójność:
   - nazwy
   - ID
   - pliki
   - `bundle_structure.json`
4. Dla single procesy nie mogą zachowywać ustawień support filament z dual.
5. Dla Inventure wspólny bundle z 2 drukarkami jest preferowanym wariantem organizacji presetów.

---

## 18. Krótki prompt startowy do nowego chatu

Można wkleić taki tekst na start nowej rozmowy:

> Pracujemy nad Zortrax Inventure.
> 
> Kontekst do zachowania:
> - aktywny patcher to `g2z_hybrid_wrapper_v10_orca_outdir_named_UPDATED.py`
> - potwierdzone offsety nagłówka `.zcode`: 54..57, 61, 62, 63, 64, 65, 66, 68..71, 73..74, 77..78, 85, 127
> - bajty 58..60 to triplet trybu zadania:
>   - single i BASF BVOH → `01 02 01`
>   - Z-SUPPORT / Z-SUPPORT Plus / Z-SUPPORT Premium → `01 03 00`
> - BASF Ultrafuse BVOH ma kod `0x17`
> - CRC jest liczone poprawnie
> - finalny wariant bundla Orca to 1 bundle z 2 drukarkami (`single`, `dual`), 8 processami i wspólnymi filamentami
> - defaulty:
>   - dual: `0.15 Quality`, `Z-PLA`, `Z-SUPPORT`
>   - single: `0.15 Quality`, `Z-PLA`
> - firmware update Inventure ma rozpoznany kontener `ZRTXUINVrNNNN`, ale payload jest nadal nieodczytany
> - przy dalszej analizie nie wolno porównywać nieekwiwalentnych plików i wyciągać z tego wniosków o polach nagłówka.

---

## 19. Najkrótsze streszczenie

Jeśli trzeba przenieść tylko absolutne minimum:

- aktywny patcher to `g2z_hybrid_wrapper_v10_orca_outdir_named_UPDATED.py`
- `58..60`:
  - single + BASF BVOH → `01 02 01`
  - Z-SUPPORT family → `01 03 00`
- `62` = model material
- `85` = support material
- `127` = CRC i jest liczone poprawnie
- `BASF Ultrafuse BVOH = 0x17`
- finalny bundle Orca: 2 drukarki (`single`, `dual`), 8 processów, wspólne filamenty
- defaulty:
  - dual = `0.15 Quality`, `Z-PLA`, `Z-SUPPORT`
  - single = `0.15 Quality`, `Z-PLA`
- firmware update ma znany kontener, ale nieznany payload
- nie wyciągać wniosków z porównań nieekwiwalentnych plików.


## A20. `Zortrax_Inventure_material_filament_db_v1.4.9.json`

```json
{
  "version": "v1.4.9/v1.2.14",
  "policy": "filament DB for Inventure; motion remains in converter markers",
  "materials": [
    {
      "filament": "BASF Ultrafuse BVOH",
      "zcode_code": "0x17",
      "external_canonical": "",
      "support_role": 1,
      "single_nozzle": 220,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 220,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "8",
      "source": "dual Inventure support role",
      "cooling_note": "Confirmed support role T1=220; triplet 01 02 01."
    },
    {
      "filament": "External ABS",
      "zcode_code": "0x81",
      "external_canonical": "ABS-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 275,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 0.8,
      "single_retract_F": 2200,
      "dual_nozzle": 275,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 0.8,
      "dual_retract_F": 2200,
      "fan_min": 0,
      "fan_max": 30,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-ABS; single Inventure + M200 Plus zcodex2, legacy/native code 0x00",
      "cooling_note": "ABS-like: low/auto fan; confirmed temps/retract from single and zcodex2."
    },
    {
      "filament": "External ASA Pro",
      "zcode_code": "0x95",
      "external_canonical": "ASA PRO-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 260,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 1.0,
      "single_retract_F": 4400,
      "dual_nozzle": 260,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 4400,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.07",
      "max_volumetric_speed": "10",
      "source": "external profile mapped from Z-ASA Pro; single Inventure; dual pair sample still missing",
      "cooling_note": "ASA/ABS-like low cooling."
    },
    {
      "filament": "External ESD",
      "zcode_code": "0x92",
      "external_canonical": "ESD PETG-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 270,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 1.8,
      "single_retract_F": 4800,
      "dual_nozzle": 270,
      "dual_chamber_as_bed": 60,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 10,
      "fan_max": 50,
      "flow_ratio": "0.97",
      "density": "1.20",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-ESD; single and dual Inventure",
      "cooling_note": "ESD PETG-like."
    },
    {
      "filament": "External FLEX",
      "zcode_code": "0x87",
      "external_canonical": "FLEX-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 230,
      "single_chamber_as_bed": 40,
      "single_retract_mm": 2.5,
      "single_retract_F": 2100,
      "dual_nozzle": 230,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.5,
      "dual_retract_F": 2100,
      "fan_min": 20,
      "fan_max": 60,
      "flow_ratio": "1.00",
      "density": "1.12",
      "max_volumetric_speed": "4",
      "source": "external profile mapped from Z-FLEX; single Inventure; dual pair sample missing",
      "cooling_note": "Flex sample confirmed in single."
    },
    {
      "filament": "External GLASS",
      "zcode_code": "0x84",
      "external_canonical": "GLASS-TYPE FILAMENT",
      "support_role": 0,
      "single_nozzle": 225,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 4800,
      "dual_nozzle": 235,
      "dual_chamber_as_bed": 60,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 15,
      "fan_max": 55,
      "flow_ratio": "0.97",
      "density": "1.27",
      "max_volumetric_speed": "9",
      "source": "external profile mapped from Z-GLASS; single and dual Inventure",
      "cooling_note": "PETG/glass-like auto cooling preserved."
    },
    {
      "filament": "External HIPS",
      "zcode_code": "0x81",
      "external_canonical": "ABS-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 235,
      "single_chamber_as_bed": 90,
      "single_retract_mm": 1.0,
      "single_retract_F": 2200,
      "dual_nozzle": 235,
      "dual_chamber_as_bed": 90,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2200,
      "fan_min": 10,
      "fan_max": 60,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "10",
      "source": "external profile mapped from Z-HIPS; inferred/existing config; sample still missing",
      "cooling_note": "Not confirmed in newest Inventure samples; kept from existing config with ABS-like retract."
    },
    {
      "filament": "External NYLON",
      "zcode_code": "0x89",
      "external_canonical": "NYLON-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 250,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 2.0,
      "single_retract_F": 4800,
      "dual_nozzle": 250,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 10,
      "fan_max": 35,
      "flow_ratio": "0.95",
      "density": "1.14",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-NYLON; single Inventure; dual pair sample missing",
      "cooling_note": "Nylon low cooling."
    },
    {
      "filament": "External PCABS",
      "zcode_code": "0x81",
      "external_canonical": "ABS-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 290,
      "single_chamber_as_bed": 85,
      "single_retract_mm": 1.2,
      "single_retract_F": 4400,
      "dual_nozzle": 290,
      "dual_chamber_as_bed": 85,
      "dual_retract_mm": 1.2,
      "dual_retract_F": 4400,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.94",
      "density": "1.10",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-PCABS; zcodex2 other printer",
      "cooling_note": "From Z-Suite zcodex2 M200 Plus; Inventure classic sample still missing."
    },
    {
      "filament": "External PEEK",
      "zcode_code": "0x12",
      "external_canonical": "PEEK-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 380,
      "single_chamber_as_bed": 140,
      "single_retract_mm": null,
      "single_retract_F": null,
      "dual_nozzle": 380,
      "dual_chamber_as_bed": 140,
      "dual_retract_mm": null,
      "dual_retract_F": null,
      "fan_min": 0,
      "fan_max": 0,
      "flow_ratio": "1.00",
      "density": "1.30",
      "max_volumetric_speed": "2",
      "source": "external profile mapped from Z-PEEK; rfid/header code known; sample missing",
      "cooling_note": "Native code known; thermal/retraction sample missing for Inventure."
    },
    {
      "filament": "External PETG",
      "zcode_code": "0x83",
      "external_canonical": "PETG-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 225,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 4800,
      "dual_nozzle": 235,
      "dual_chamber_as_bed": 60,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 15,
      "fan_max": 60,
      "flow_ratio": "0.97",
      "density": "1.27",
      "max_volumetric_speed": "9",
      "source": "external profile mapped from Z-PETG; single and dual Inventure",
      "cooling_note": "PETG auto cooling preserved."
    },
    {
      "filament": "External PHA",
      "zcode_code": "0x86",
      "external_canonical": "PLA-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 205,
      "single_chamber_as_bed": 55,
      "single_retract_mm": 1.0,
      "single_retract_F": 2000,
      "dual_nozzle": 205,
      "dual_chamber_as_bed": 55,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 35,
      "fan_max": 100,
      "flow_ratio": "0.98",
      "density": "1.24",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-PHA; inferred/existing config; sample still missing",
      "cooling_note": "No newest native sample; PLA/PHA-like cooling retained."
    },
    {
      "filament": "External PLA",
      "zcode_code": "0x86",
      "external_canonical": "PLA-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 210,
      "single_chamber_as_bed": 30,
      "single_retract_mm": 1.0,
      "single_retract_F": 2000,
      "dual_nozzle": 210,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 30,
      "fan_max": 100,
      "flow_ratio": "0.98",
      "density": "1.24",
      "max_volumetric_speed": "12",
      "source": "external profile mapped from Z-PLA; single and dual Inventure",
      "cooling_note": "PLA; dual chamber higher than single in support jobs."
    },
    {
      "filament": "External PLA Pro",
      "zcode_code": "0x94",
      "external_canonical": "PLA PRO-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 207,
      "single_chamber_as_bed": 30,
      "single_retract_mm": 1.5,
      "single_retract_F": 2100,
      "dual_nozzle": 210,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 25,
      "fan_max": 100,
      "flow_ratio": "0.98",
      "density": "1.24",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-PLA Pro; single and dual Inventure",
      "cooling_note": "PLA Pro; dual chamber higher than single in support jobs."
    },
    {
      "filament": "External SEMIFLEX",
      "zcode_code": "0x96",
      "external_canonical": "SEMIFLEX-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 225,
      "single_chamber_as_bed": 50,
      "single_retract_mm": 2.0,
      "single_retract_F": 2500,
      "dual_nozzle": 225,
      "dual_chamber_as_bed": 50,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 2500,
      "fan_min": 20,
      "fan_max": 60,
      "flow_ratio": "1.00",
      "density": "1.12",
      "max_volumetric_speed": "4",
      "source": "external profile mapped from Z-SEMIFLEX; dual Inventure; single inferred from dual",
      "cooling_note": "Semi-flex dual sample confirmed; single classic sample still missing."
    },
    {
      "filament": "External SUPPORT",
      "zcode_code": "0x07",
      "external_canonical": "Z-SUPPORT",
      "support_role": 1,
      "single_nozzle": 220,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 220,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "4",
      "source": "external profile mapped from Z-SUPPORT; inferred support-role; direct sample missing",
      "cooling_note": "Support role; chamber is fallback, real dual chamber should come from model pair."
    },
    {
      "filament": "External SUPPORT Plus",
      "zcode_code": "0x0D",
      "external_canonical": "Z-SUPPORT PLUS",
      "support_role": 1,
      "single_nozzle": 220,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 220,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "4",
      "source": "external profile mapped from Z-SUPPORT Plus; inferred support-role; direct sample missing",
      "cooling_note": "Support role; chamber fallback only."
    },
    {
      "filament": "External SUPPORT Premium",
      "zcode_code": "0x11",
      "external_canonical": "Z-SUPPORT PREMIUM",
      "support_role": 1,
      "single_nozzle": 220,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 220,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-SUPPORT Premium; dual Inventure support role",
      "cooling_note": "Confirmed support role T1=220; chamber comes from model/support job, not standalone support."
    },
    {
      "filament": "External ULTRAT",
      "zcode_code": "0x91",
      "external_canonical": "ULTRAT-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 260,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 1.0,
      "single_retract_F": 4400,
      "dual_nozzle": 260,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 3000,
      "fan_min": 10,
      "fan_max": 80,
      "flow_ratio": "0.926",
      "density": "1.04",
      "max_volumetric_speed": "12",
      "source": "external profile mapped from Z-ULTRAT; single Inventure; M300 Dual zcodex2 for ATP pair",
      "cooling_note": "ULTRAT/ABS-like; dual retract from zcodex2 ATP sample, single from Inventure."
    },
    {
      "filament": "External ULTRAT Plus",
      "zcode_code": "0x91",
      "external_canonical": "ULTRAT-BASED FILAMENT",
      "support_role": 0,
      "single_nozzle": 260,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 1.0,
      "single_retract_F": 4400,
      "dual_nozzle": 260,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 10,
      "fan_max": 80,
      "flow_ratio": "0.926",
      "density": "1.04",
      "max_volumetric_speed": "8",
      "source": "external profile mapped from Z-ULTRAT Plus; single and dual Inventure",
      "cooling_note": "High-temp ABS-like; dual retract differs from single in native samples."
    },
    {
      "filament": "Z-ABS",
      "zcode_code": "0x00",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 275,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 0.8,
      "single_retract_F": 2200,
      "dual_nozzle": 275,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 0.8,
      "dual_retract_F": 2200,
      "fan_min": 0,
      "fan_max": 30,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "8",
      "source": "single Inventure + M200 Plus zcodex2, legacy/native code 0x00",
      "cooling_note": "ABS-like: low/auto fan; confirmed temps/retract from single and zcodex2."
    },
    {
      "filament": "Z-ASA Pro",
      "zcode_code": "0x0C",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 260,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 1.0,
      "single_retract_F": 4400,
      "dual_nozzle": 260,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 4400,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.07",
      "max_volumetric_speed": "10",
      "source": "single Inventure; dual pair sample still missing",
      "cooling_note": "ASA/ABS-like low cooling."
    },
    {
      "filament": "Z-ESD",
      "zcode_code": "0x08",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 270,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 1.8,
      "single_retract_F": 4800,
      "dual_nozzle": 270,
      "dual_chamber_as_bed": 60,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 10,
      "fan_max": 50,
      "flow_ratio": "0.97",
      "density": "1.20",
      "max_volumetric_speed": "8",
      "source": "single and dual Inventure",
      "cooling_note": "ESD PETG-like."
    },
    {
      "filament": "Z-FLEX",
      "zcode_code": "0x0F",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 230,
      "single_chamber_as_bed": 40,
      "single_retract_mm": 2.5,
      "single_retract_F": 2100,
      "dual_nozzle": 230,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.5,
      "dual_retract_F": 2100,
      "fan_min": 20,
      "fan_max": 60,
      "flow_ratio": "1.00",
      "density": "1.12",
      "max_volumetric_speed": "4",
      "source": "single Inventure; dual pair sample missing",
      "cooling_note": "Flex sample confirmed in single."
    },
    {
      "filament": "Z-GLASS",
      "zcode_code": "0x02",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 225,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 4800,
      "dual_nozzle": 235,
      "dual_chamber_as_bed": 60,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 15,
      "fan_max": 55,
      "flow_ratio": "0.97",
      "density": "1.27",
      "max_volumetric_speed": "9",
      "source": "single and dual Inventure",
      "cooling_note": "PETG/glass-like auto cooling preserved."
    },
    {
      "filament": "Z-HIPS",
      "zcode_code": "0x03",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 235,
      "single_chamber_as_bed": 90,
      "single_retract_mm": 1.0,
      "single_retract_F": 2200,
      "dual_nozzle": 235,
      "dual_chamber_as_bed": 90,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2200,
      "fan_min": 10,
      "fan_max": 60,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "10",
      "source": "inferred/existing config; sample still missing",
      "cooling_note": "Not confirmed in newest Inventure samples; kept from existing config with ABS-like retract."
    },
    {
      "filament": "Z-NYLON",
      "zcode_code": "0x10",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 250,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 2.0,
      "single_retract_F": 4800,
      "dual_nozzle": 250,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 10,
      "fan_max": 35,
      "flow_ratio": "0.95",
      "density": "1.14",
      "max_volumetric_speed": "8",
      "source": "single Inventure; dual pair sample missing",
      "cooling_note": "Nylon low cooling."
    },
    {
      "filament": "Z-PCABS",
      "zcode_code": "0x04",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 290,
      "single_chamber_as_bed": 85,
      "single_retract_mm": 1.2,
      "single_retract_F": 4400,
      "dual_nozzle": 290,
      "dual_chamber_as_bed": 85,
      "dual_retract_mm": 1.2,
      "dual_retract_F": 4400,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.94",
      "density": "1.10",
      "max_volumetric_speed": "8",
      "source": "zcodex2 other printer",
      "cooling_note": "From Z-Suite zcodex2 M200 Plus; Inventure classic sample still missing."
    },
    {
      "filament": "Z-PEEK",
      "zcode_code": "0x12",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 380,
      "single_chamber_as_bed": 140,
      "single_retract_mm": null,
      "single_retract_F": null,
      "dual_nozzle": 380,
      "dual_chamber_as_bed": 140,
      "dual_retract_mm": null,
      "dual_retract_F": null,
      "fan_min": 0,
      "fan_max": 0,
      "flow_ratio": "1.00",
      "density": "1.30",
      "max_volumetric_speed": "2",
      "source": "rfid/header code known; sample missing",
      "cooling_note": "Native code known; thermal/retraction sample missing for Inventure."
    },
    {
      "filament": "Z-PETG",
      "zcode_code": "0x05",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 225,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 4800,
      "dual_nozzle": 235,
      "dual_chamber_as_bed": 60,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 4800,
      "fan_min": 15,
      "fan_max": 60,
      "flow_ratio": "0.97",
      "density": "1.27",
      "max_volumetric_speed": "9",
      "source": "single and dual Inventure",
      "cooling_note": "PETG auto cooling preserved."
    },
    {
      "filament": "Z-PHA",
      "zcode_code": "0x09",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 205,
      "single_chamber_as_bed": 55,
      "single_retract_mm": 1.0,
      "single_retract_F": 2000,
      "dual_nozzle": 205,
      "dual_chamber_as_bed": 55,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 35,
      "fan_max": 100,
      "flow_ratio": "0.98",
      "density": "1.24",
      "max_volumetric_speed": "8",
      "source": "inferred/existing config; sample still missing",
      "cooling_note": "No newest native sample; PLA/PHA-like cooling retained."
    },
    {
      "filament": "Z-PLA",
      "zcode_code": "0x0A",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 210,
      "single_chamber_as_bed": 30,
      "single_retract_mm": 1.0,
      "single_retract_F": 2000,
      "dual_nozzle": 210,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 30,
      "fan_max": 100,
      "flow_ratio": "0.98",
      "density": "1.24",
      "max_volumetric_speed": "12",
      "source": "single and dual Inventure",
      "cooling_note": "PLA; dual chamber higher than single in support jobs."
    },
    {
      "filament": "Z-PLA Pro",
      "zcode_code": "0x0B",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 207,
      "single_chamber_as_bed": 30,
      "single_retract_mm": 1.5,
      "single_retract_F": 2100,
      "dual_nozzle": 210,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 25,
      "fan_max": 100,
      "flow_ratio": "0.98",
      "density": "1.24",
      "max_volumetric_speed": "8",
      "source": "single and dual Inventure",
      "cooling_note": "PLA Pro; dual chamber higher than single in support jobs."
    },
    {
      "filament": "Z-SEMIFLEX",
      "zcode_code": "0x0E",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 225,
      "single_chamber_as_bed": 50,
      "single_retract_mm": 2.0,
      "single_retract_F": 2500,
      "dual_nozzle": 225,
      "dual_chamber_as_bed": 50,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 2500,
      "fan_min": 20,
      "fan_max": 60,
      "flow_ratio": "1.00",
      "density": "1.12",
      "max_volumetric_speed": "4",
      "source": "dual Inventure; single inferred from dual",
      "cooling_note": "Semi-flex dual sample confirmed; single classic sample still missing."
    },
    {
      "filament": "Z-SUPPORT",
      "zcode_code": "0x07",
      "external_canonical": "",
      "support_role": 1,
      "single_nozzle": 220,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 220,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "4",
      "source": "inferred support-role; direct sample missing",
      "cooling_note": "Support role; chamber is fallback, real dual chamber should come from model pair."
    },
    {
      "filament": "Z-SUPPORT ATP",
      "zcode_code": "0x13",
      "external_canonical": "",
      "support_role": 1,
      "single_nozzle": 250,
      "single_chamber_as_bed": 90,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 250,
      "dual_chamber_as_bed": 90,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "4",
      "source": "M300 Dual zcodex2 experimental; not confirmed Inventure classic",
      "cooling_note": "EXPERIMENTAL for Inventure; code observed in M300 Dual zcodex2 only."
    },
    {
      "filament": "Z-SUPPORT Plus",
      "zcode_code": "0x0D",
      "external_canonical": "",
      "support_role": 1,
      "single_nozzle": 220,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 220,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "4",
      "source": "inferred support-role; direct sample missing",
      "cooling_note": "Support role; chamber fallback only."
    },
    {
      "filament": "Z-SUPPORT Premium",
      "zcode_code": "0x11",
      "external_canonical": "",
      "support_role": 1,
      "single_nozzle": 220,
      "single_chamber_as_bed": 60,
      "single_retract_mm": 2.0,
      "single_retract_F": 3600,
      "dual_nozzle": 220,
      "dual_chamber_as_bed": 40,
      "dual_retract_mm": 2.0,
      "dual_retract_F": 3600,
      "fan_min": 10,
      "fan_max": 40,
      "flow_ratio": "0.95",
      "density": "1.04",
      "max_volumetric_speed": "8",
      "source": "dual Inventure support role",
      "cooling_note": "Confirmed support role T1=220; chamber comes from model/support job, not standalone support."
    },
    {
      "filament": "Z-ULTRAT",
      "zcode_code": "0x01",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 260,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 1.0,
      "single_retract_F": 4400,
      "dual_nozzle": 260,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 3000,
      "fan_min": 10,
      "fan_max": 80,
      "flow_ratio": "0.926",
      "density": "1.04",
      "max_volumetric_speed": "12",
      "source": "single Inventure; M300 Dual zcodex2 for ATP pair",
      "cooling_note": "ULTRAT/ABS-like; dual retract from zcodex2 ATP sample, single from Inventure."
    },
    {
      "filament": "Z-ULTRAT Plus",
      "zcode_code": "0x06",
      "external_canonical": "",
      "support_role": 0,
      "single_nozzle": 260,
      "single_chamber_as_bed": 80,
      "single_retract_mm": 1.0,
      "single_retract_F": 4400,
      "dual_nozzle": 260,
      "dual_chamber_as_bed": 80,
      "dual_retract_mm": 1.0,
      "dual_retract_F": 2000,
      "fan_min": 10,
      "fan_max": 80,
      "flow_ratio": "0.926",
      "density": "1.04",
      "max_volumetric_speed": "8",
      "source": "single and dual Inventure",
      "cooling_note": "High-temp ABS-like; dual retract differs from single in native samples."
    }
  ]
}
```


## A21. `Zortrax_Inventure_Orca_presets_v1.4.14_current_converter_report.md`

# Zortrax Inventure Orca presets — v1.4.14 current converter

Generated: 2026-05-05T07:00:59

Source base: `v1.4.9_ZSuite_filament_db` presets.
Target converter: `v1.4.14_auto_temp_speed_scale_policy`.

## Main update

These presets update `printer` Machine G-code to the current AUTO policy:

- `CHAMBER=AUTO`
- `T0_TEMP=AUTO`
- `T1_TEMP=AUTO` for dual
- `E_SPEED_SCALE=AUTO`
- `RETRACT_SPEED_SCALE=AUTO`
- `TEMP=AUTO` in toolchange/layer clean
- `ZORTRAX_LAYER_META` retained for seam `0xDF`
- `ZSUITE HINTS` schema set to `2`
- `profile_suffix_policy=CANONICAL_PREFIX_PLUS_USER_SUFFIX_ALLOWED`
- `zortrax_temperature_policy=ORCA_OVERRIDES_ZSUITE_DEFAULTS`
- `zortrax_chamber_source=ORCA_BED_AS_CHAMBER`

Temperature priority in the converter:

1. explicit value in marker, for example `T0_TEMP=215` or `CHAMBER=45`
2. current Orca metadata / current filament settings
3. Z-Suite material/pair default in converter database
4. fallback

AUTO speed-scale policy applies only to Zortrax technical procedures generated by converter: start, start-purge, toolchange-clean, layer-clean. It does not change normal print speeds from process.

## Post-process path

Current generated presets use Windows path:

```text
"C:\Users\Marcin Kowalik\OrcaScripts\run_g2z_orca_postprocess.bat"
```

For macOS replace process `post_process` with:

```text
"/Users/mkowalik/OrcaScripts/run_g2z_orca_postprocess.command"
```

## Files

- `Zortrax Inventure 0.4 nozzle - single_v1.4.14_current_converter.orca_printer`
- `Zortrax Inventure 0.4 nozzle - dual_v1.4.14_current_converter.orca_printer`

## Validation

- ZIP test: OK
- JSON parse: OK
- `bundle_structure.json` present: OK

## SHA256

```text
Zortrax Inventure 0.4 nozzle - single_v1.4.14_current_converter.orca_printer: 1bd4658da362a4d86b4929c72b2b6bba1d901cd2a3bf6256733e5232e29274c3
Zortrax Inventure 0.4 nozzle - dual_v1.4.14_current_converter.orca_printer: 4f1a97218d67a4278b4da6117c214991f06549f7fcf6388c5709847acebbeafa
```

## Changed printer snippets

### Single start

```gcode
;ZORTRAX_START_MACHINE SINGLE CHAMBER=AUTO T0_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO
```

### Single layer change

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
;ZORTRAX_LAYER_META layer_num={layer_num} layer_z={layer_z}
```

### Dual start

```gcode
;ZORTRAX_START_MACHINE DUAL CHAMBER=AUTO T0_TEMP=AUTO T1_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO
```

### Dual toolchange

```gcode
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} direction_model_support={previous_extruder}->{next_extruder} zsuite_direction=AUTO layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400
```

### Dual layer change

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN DUAL EVERY=20 START_LAYER=10 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
;ZORTRAX_LAYER_META layer_num={layer_num} layer_z={layer_z}
```

## Preserved from v1.4.9

- full filament database with Z-Suite-derived temperatures/retractions where known
- `chamber=bed` mapping for Inventure
- `ZORTRAX_FILAMENT_PROFILE` comments in filament Advanced
- OP02 speed-derived process speed fields
- Z-ABS legacy `0x00`, Z-PEEK `0x12`, experimental Z-SUPPORT ATP `0x13`
- process speeds/accelerations/jerk structure preserved
- single support filament set to 0; dual support filament set to 2


## A22. `Zortrax_Inventure_Orca_presets_v1.4.6_report.md`

# Zortrax Inventure Orca presets v1.4.6 — chamber_as_bed
Zakres: przebudowa ostatnich presetów single/dual z zachowaniem najnowszych ustaleń: ZSUITE hints, LAYER_META dla seam, single T0 clean safe, dual toolchange clean oraz zasada `chamber = bed`.
## Pliki wejściowe
- `Zortrax Inventure 0.4 nozzle - single.orca_printer`
- `Zortrax Inventure 0.4 nozzle - dual.orca_printer`
## Pliki wynikowe
- `Zortrax Inventure 0.4 nozzle - single_v1.4.6_chamber_as_bed.orca_printer` — SHA256 `cd25d7f87fb54782f4a67665dc0f1d372b082db000ec2ca80828a3ed500744dc`
- `Zortrax Inventure 0.4 nozzle - dual_v1.4.6_chamber_as_bed.orca_printer` — SHA256 `bf448222ca47079ceabf6a8c8abc74b37e953143cb4b74a6d542eaeeb6c5dc56`

## Najważniejsze zmiany
- `file_start_gcode` zawiera pełny blok `ORCA METADATA` + `ZORTRAX ZSUITE HINTS`.
- Dodano jawne flagi `zortrax_chamber_as_bed=1`, `chamber_equals_bed=1`, `zsuite_chamber_as_bed=1`.
- Single ma potwierdzony layer clean: `G92 E0`, `ZORTRAX_LAYER_CLEAN ...`, `ZORTRAX_LAYER_META layer_num/layer_z`.
- Dual ma pełny `ZORTRAX_TOOLCHANGE_META` + `ZORTRAX_TOOLCHANGE_CLEAN` i `ZORTRAX_LAYER_META`.
- Wszystkie profile filamentów: `activate_chamber_temp_control=1`; wszystkie plate-temp placeholdery są zrównane z efektywną komorą (`chamber=bed`). Efektywna komora jest brana z istniejącego `chamber_temperature`, a jeśli go nie było — z normalnego `hot_plate_temp`.
- Wszystkie processy mają zunifikowany post-process na macOS: `/Users/mkowalik/OrcaScripts/run_g2z_orca_postprocess.command`.
- Single process: `support_filament=0`, `support_interface_filament=0`; dual process: `support_filament=2`, `support_interface_filament=2`.

## Walidacja
- `Zortrax Inventure 0.4 nozzle - single_v1.4.6_chamber_as_bed.orca_printer` testzip: OK
- `Zortrax Inventure 0.4 nozzle - single_v1.4.6_chamber_as_bed.orca_printer` json: OK
- `Zortrax Inventure 0.4 nozzle - dual_v1.4.6_chamber_as_bed.orca_printer` testzip: OK
- `Zortrax Inventure 0.4 nozzle - dual_v1.4.6_chamber_as_bed.orca_printer` json: OK

## Zmiany filamentów — przykład chamber=bed
- `filament/BASF Ultrafuse BVOH.json`: filament chamber=bed {'chamber': '95', 'hot': '95', 'textured': '95', 'eng': '0'}->{'chamber': '95', 'hot': '95', 'textured': '95', 'eng': '95'}
- `filament/External ASA Pro.json`: filament chamber=bed {'chamber': '0', 'hot': '100', 'textured': '100', 'eng': '100'}->{'chamber': '100', 'hot': '100', 'textured': '100', 'eng': '100'}
- `filament/External ESD.json`: filament chamber=bed {'chamber': '0', 'hot': '80', 'textured': '80', 'eng': '80'}->{'chamber': '80', 'hot': '80', 'textured': '80', 'eng': '80'}
- `filament/External FLEX.json`: filament chamber=bed {'chamber': '0', 'hot': '60', 'textured': '60', 'eng': '60'}->{'chamber': '60', 'hot': '60', 'textured': '60', 'eng': '60'}
- `filament/Z-ULTRAT Plus.json`: filament chamber=bed {'chamber': '100', 'hot': '80', 'textured': '95', 'eng': '100'}->{'chamber': '100', 'hot': '100', 'textured': '100', 'eng': '100'}


## A23. `Zortrax_Inventure_Orca_presets_v1.4.8_OP02_speed_scaling_report.md`

# Zortrax Inventure Orca presets v1.4.8 — OP02 speed semantics v2

Bazą były presety `v1.4.7_ZSuite_OP02_speeds`. Zachowano wszystkie istniejące pola w `printer`, `filament`, `process` i `bundle_structure.json`; zmieniono tylko opisane pola prędkości i notatki audytowe.

## Korekta względem v1.4.7

- `support_speed` oparto na obszarach `0x04/0x05/0x18`, które w parze `b1/b3` reagują na `Print speed * Support Print speed`.
- `support_interface_speed` oparto na obszarach `0x1B/0x21`, które reagują na globalny `Print speed`, ale nie na `Support Print speed`.
- `wipe_tower_max_purge_speed` nadal `33 mm/s` z `F2000`; travel `120 mm/s` z `F7200`.
- Akceleracje/jerk zachowane — brak wiarygodnej tabeli acceleration w classic `.zcode`.

## Docelowe prędkości [mm/s]

| mode | layer | outer | inner | internal | sparse | top | support | support interface | travel | tower |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single | 0.08 | 12 | 17 | 41 | 28 | 28 | 40 | 35 | 120 | 33 |
| single | 0.15 | 20 | 25 | 40 | 25 | 33 | 40 | 35 | 120 | 33 |
| single | 0.20 | 20 | 25 | 40 | 40 | 40 | 40 | 35 | 120 | 33 |
| single | 0.30 | 20 | 25 | 40 | 40 | 40 | 40 | 35 | 120 | 33 |
| dual | 0.08 | 10 | 29 | 53 | 54 | 33 | 58 | 35 | 120 | 33 |
| dual | 0.15 | 20 | 58 | 107 | 108 | 67 | 58 | 35 | 120 | 33 |
| dual | 0.20 | 20 | 58 | 103 | 108 | 67 | 58 | 35 | 120 | 33 |
| dual | 0.30 | 19 | 25 | 40 | 40 | 40 | 58 | 40 | 120 | 33 |

## Walidacja

- ZIP/JSON/bundle_structure: OK dla single i dual.


## A24. `Zortrax_Inventure_Orca_presets_v1.4.9_filament_db_report.md`

# Zortrax Inventure Orca presets v1.4.9 — filament DB update

Zakres: aktualizacja sekcji **filament** pod Inventure na bazie natywnych próbek Z-Suite single/dual, `b1/b3`, `zcodex2` jako źródeł pomocniczych, oraz bieżących ustaleń projektu.

## Co zostało uzupełnione w filamentach

- **Temperature / chamber-as-bed**: `nozzle_temperature`, `nozzle_temperature_initial_layer`, `chamber_temperature` oraz wszystkie pola Orca plate temp zostały ustawione spójnie. Dla Inventure wartości `bed/plate` są nośnikiem temperatury komory.
- **Settings override / retrakcja**: tam gdzie próbki Z-Suite potwierdziły normalną retrakcję materiałową, ustawiono `filament_retraction_length`, `filament_retraction_speed`, `filament_deretraction_speed` i `filament_retract_restart_extra=0`.
- **Cooling**: uzupełniono konserwatywne klasy fan Auto na podstawie klasy materiału. Dokładna krzywa `Fan speed Auto` Z-Suite nie jest jawnie wyciągnięta, więc te wartości są profilem zgodnym klasowo, nie binarnym odczytem z Z-Suite.
- **Advanced**: w `filament_start_gcode` dodano tylko komentarz `;ZORTRAX_FILAMENT_PROFILE ...`. Nie ma tam ruchów, `M104/M109`, purge ani toolchange. Ruchy nadal kontroluje konwerter/printer G-code.
- **Multimaterial**: ustawienia tower/purge pozostawiono bezpieczne; fizyczny bin purge/clean nadal obsługuje konwerter, a nie Orca filament G-code.
- **Dependencies**: zachowano kompatybilność z printer presetami i `from=User`.

## Nowe filamenty dodane do configów

- `Z-ABS` — legacy/native code `0x00`, potwierdzony w single / zcodex2.
- `Z-PEEK` — native code `0x12`, profil termiczny nadal oznaczony jako niepotwierdzony próbką Inventure classic.
- `Z-SUPPORT ATP` — eksperymentalny support `0x13`, potwierdzony w `.zcodex2` M300 Dual, niepotwierdzony jeszcze dla Inventure classic/RFID.

## Czego nie da się dobrze zasymulować samą zakładką Filament w Orca

1. Firmware'owego startu Inventure: kosz, potwierdzenie, homing XY/Z, przejścia `03 1A/03 15` — zostaje w konwerterze.
2. Bin/waste purge-clean nad pojemnikiem — to nie jest drukowana wieża i nie powinno być w filament gcode.
3. Toolchange clean T1→T0/T0→T1 z `SELECT`, pozycjami `03 11`, `F4/FE/FD`, dwell i restore — zostaje w `ZORTRAX_TOOLCHANGE_CLEAN`.
4. Single T0 clean bez dualowego `F4/DWELL` — zostaje w `ZORTRAX_LAYER_CLEAN` i potwierdzonej logice v1.4.2+.
5. Pełnej krzywej `Fan speed Auto` Z-Suite — w próbkach tekstowo widzimy Auto, ale nie kompletną krzywą per warstwa/feature.
6. Akceleracji per-feature Z-Suite — OP02 daje feedrate, ale nie pełną tabelę acceleration/jerk.
7. Chamber jako prawdziwy obiekt sprzętowy — Orca ma bed/plate i chamber, dlatego stosujemy mapowanie `chamber=bed`, a realną interpretację robi konwerter.

## Ważne reguły trybu single/dual

- Dla modelowych materiałów wartości single i dual mogą być różne. Przykład: `Z-PLA` single ma chamber 30°C, a dual z supportem 40°C.
- Support-role `Z-SUPPORT Premium` / `BASF BVOH` ma T1=220°C, ale nie powinien narzucać wysokiej komory; chamber job-level pochodzi z pary model+support.
- `Z-SUPPORT ATP` jest eksperymentalny.

## Walidacja

- Single ZIP/JSON: OK
- Dual ZIP/JSON: OK
- `bundle_structure.json`: uzupełniony o nowe filamenty.

## Liczby

- Single filamenty zaktualizowane/dodane: 39
- Dual filamenty zaktualizowane/dodane: 39



## A25. `ZORTRAX_INVENTURE_podsumowanie_chatu_homing_kalibracja_2026-04-27.md`

# ZORTRAX INVENTURE — podsumowanie chatu do przeniesienia

Data: 2026-04-27  
Zakres: **Nozzle Alignment Calibration, Platform/Bed Leveling, homing osi X/Y/Z i test aktualnego konwertera `g2z_wrapper_orca.py` v1.07**

---

## 1. Cel rozmowy

W tym wątku sprawdzano, czy w Zortrax Inventure da się z poziomu `.zcode`, G-code albo firmware wywołać przed wydrukiem:

1. procedurę **Nozzle Alignment Calibration**,
2. procedurę **Platform / Bed Leveling**,
3. homing wszystkich osi, szczególnie osi **Z**,
4. oraz jak aktualny konwerter `g2z_wrapper_orca.py` generuje komendy homingu na przykładowych plikach.

---

## 2. Nozzle Alignment Calibration — ustalenie

### Wniosek

Nie znaleziono potwierdzonego sposobu wywołania firmware’owej procedury:

```text
Maintenance → Nozzle Alignment Calibration
```

z poziomu:

- G-code,
- `.zcode`,
- znanego opcode,
- markera konwertera,
- ani bezpośrednio z firmware update.

### Co wiadomo

Oficjalna procedura Zortraxa jest interaktywna:

1. użytkownik uruchamia ją z menu drukarki,
2. drukarka drukuje dwa modele kalibracyjne,
3. każdy model ma układ 13 linii materiału modelowego i 13 linii supportu,
4. użytkownik wybiera na ekranie najlepiej pokrywającą się parę linii,
5. firmware zapisuje offset między głowicami.

### Najważniejszy wniosek praktyczny

Można odtworzyć **wydruk wzorca kontrolnego** w `.zcode`, ale to nie jest to samo co oryginalna procedura z menu, ponieważ:

- wzorzec kontrolny nie zapisze offsetu w firmware,
- nie ma znanej komendy typu `CALL_NOZZLE_ALIGNMENT`,
- zapis offsetu odbywa się prawdopodobnie przez interaktywną logikę UI firmware.

---

## 3. Platform / Bed Leveling — ustalenie

### Wniosek

Nie znaleziono potwierdzonej komendy G-code / `.zcode`, która uruchamia oryginalną procedurę:

```text
Maintenance → Platform Leveling
```

przed właściwym wydrukiem.

### Co wiadomo

W Inventure leveling jest procedurą interaktywną:

1. drukarka sprawdza odległość dyszy w punktach platformy,
2. pokazuje instrukcje użytkownikowi,
3. użytkownik reguluje śruby platformy,
4. procedura jest uruchamiana z menu drukarki.

To nie wygląda jak zwykłe automatyczne `G29` znane z drukarek Marlin.

### Najważniejszy wniosek praktyczny

Nie należy zakładać, że można dopisać do start G-code np.:

```gcode
G29
```

i uzyskać firmware’owy bed leveling Inventure. Na obecnym etapie nie ma potwierdzonego odpowiednika.

---

## 4. Możliwe obejście: pre-print alignment check

Chociaż nie da się obecnie potwierdzić wywołania oryginalnych procedur firmware, można dodać do konwertera własny **pre-print check**.

### Proponowana logika

Przed właściwym modelem można wygenerować:

1. start machine,
2. nagrzanie,
3. czyszczenie dysz,
4. krótki wydruk testowy T0/T1 w rogu platformy,
5. pauzę / oczekiwanie,
6. decyzję użytkownika:
   - jeśli linie są OK → kontynuować,
   - jeśli offset jest zły → anulować wydruk i wykonać prawdziwą kalibrację z menu.

### Ważne ograniczenie

Taki pre-print check:

- pozwala wykryć problem przed długim wydrukiem,
- ale **nie kalibruje firmware**,
- nie zapisuje offsetu między głowicami,
- nie zastępuje `Maintenance → Nozzle Alignment Calibration`.

---

## 5. Firmware update — status

Wcześniejsze ustalenia projektu nadal obowiązują:

- `InventureUpdate.bin` ma rozpoznany kontener:
  - `ZRTX`,
  - `UINV`,
  - rewizja `rNNNN`,
  - dalej payload od offsetu `0x15`,
- payload ma wysoką entropię,
- nie zawiera jawnych stringów,
- nie wygląda jak prosty ZIP/gzip/LZMA/ELF,
- prawdopodobnie jest szyfrowany lub opakowany,
- z firmware update nie udało się wydobyć listy komend ani funkcji kalibracyjnych.

Wniosek: firmware na ten moment nie daje praktycznej ścieżki do znalezienia komendy `Nozzle Alignment` lub `Platform Leveling`.

---

## 6. Homing osi — najważniejszy problem

Użytkownik zauważył, że po wybraniu pliku drukarka robi tylko homing X/Y, następnie zaczyna nagrzewać ekstrudery, a nie wykonuje wyraźnego homingu osi Z.

### Ustalenie robocze

Dla Inventure znana komenda homingu w classic `.zcode` to:

```text
cmd 5 = MoveToStart / homing
```

Payload osi jest bitowy:

```text
X = 0x01
Y = 0x02
Z = 0x04
```

Czyli:

```text
X + Y     = 0x03
Z         = 0x04
X + Y + Z = 0x07
```

Najbardziej zgodny z referencją Z-Suite układ to rozdzielone:

```text
03 05 03 dd   ; home X/Y
03 05 04 89   ; home Z
```

---

## 7. Test aktualnego konwertera `g2z_wrapper_orca.py`

Użytkownik przesłał najnowszy plik:

```text
g2z_wrapper_orca.py
```

Wersja w pliku:

```text
v1.07-full-orca-placeholders
```

Najważniejsze funkcje tej wersji:

- obsługa `;ZORTRAX_START_MACHINE`,
- obsługa `;ZORTRAX_SPECIAL_CLEAN`,
- obsługa `;ZORTRAX_SPECIAL_POS`,
- obsługa `;ZORTRAX_END_MACHINE`,
- obsługa rozszerzonych placeholderów Orca,
- obsługa `PURGE=AUTO`,
- obsługa `IDLE_RETRACT=AUTO`,
- czyszczenie głowic sekwencjami podobnymi do Z-Suite,
- start/end machine sekwencjami podobnymi do Z-Suite.

---

## 8. Test: `;ZORTRAX_START_MACHINE AUTO`

Dla minimalnych plików testowych z markerem:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

konwerter generuje prawidłową sekwencję startową Z-Suite-like.

### Wynik dla single

W strumieniu `.zcode` pojawia się:

```text
03 05 03 dd   ; home X/Y
03 05 04 89   ; home Z
```

### Wynik dla dual

W strumieniu `.zcode` pojawia się tak samo:

```text
03 05 03 dd   ; home X/Y
03 05 04 89   ; home Z
```

### Wniosek

Jeżeli w Orca wstawiony jest marker:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

to aktualny konwerter ma wbudowany homing X/Y oraz Z zgodny z sekwencją referencyjną Z-Suite.

---

## 9. Test: zwykły G-code z `G28`

Dla testowego G-code:

```gcode
G28
G28 X0 Y0
G28 Z0
```

konwerter wygenerował:

```text
G28        → 03 05 7f 61
G28 X0 Y0  → 03 05 03 dd
G28 Z0     → 03 05 04 89
```

### Problem

Gołe:

```gcode
G28
```

nie jest mapowane na znany, bezpieczny układ Z-Suite:

```text
03 05 03 dd
03 05 04 89
```

ani nawet tylko na `X/Y/Z = 0x07`.

Zamiast tego aktualny kod traktuje brak parametrów jako wszystkie osie:

```text
X, Y, Z, E, A, B, Z2
```

co daje bitfield:

```text
0x7F
```

i wynik:

```text
03 05 7f 61
```

### Wniosek

To jest potencjalny błąd lub przynajmniej niepożądane zachowanie w obsłudze zwykłego `G28`.

---

## 10. Test na przykładowym pliku ze źródeł

Na przykładowym pliku:

```text
Inventure_0.15_Z-ULTRAT_Z-ULTRAT_1h4m single2.gcode
```

aktualny konwerter wygenerował `.zcode` z dwoma komendami homingu:

```text
na początku: 03 05 7f 61
na końcu:    03 05 03 dd
```

W tym konkretnym wyniku nie było osobnego:

```text
03 05 04 89
```

czyli nie było wyraźnego osobnego `home Z`.

### Interpretacja

Ten plik prawdopodobnie nie korzystał z markera:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

tylko ze zwykłego `G28`.

Dlatego poszedł przez ogólną obsługę `G28`, która obecnie generuje `0x7F`.

---

## 11. Najważniejsze zalecenie dla Orca

W **Machine start G-code** dla Inventure należy obecnie używać markera:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

a nie polegać na ręcznym:

```gcode
G28
```

Najbardziej aktualna integracja Orca powinna wyglądać tak:

Start G-code:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

Tool change / change filament:

```gcode
;ZORTRAX_SPECIAL_CLEAN AUTO
```

End G-code:

```gcode
;ZORTRAX_END_MACHINE AUTO
```

To daje największą szansę na zachowanie podobne do Z-Suite, bo marker startu wstawia natywne sekwencje Z-Suite-like, w tym:

```text
home X/Y
home Z
```

---

## 12. Zalecana poprawka w konwerterze

W aktualnym `g2z_wrapper_orca.py` należy poprawić obsługę `G28`.

### Obecne zachowanie

Dla `G28` bez parametrów aktualna logika odpowiada temu:

```python
vals = {a: Decimal(0) for a in ("X", "Y", "Z", "E", "A", "B", "Z2")}
```

To skutkuje bitfieldem `0x7F`.

### Zalecane zachowanie

Dla `G28` bez parametrów najlepiej generować sekwencję jak Z-Suite:

```text
03 05 03 dd   ; home X/Y
03 05 04 89   ; home Z
```

czyli logicznie:

```python
if cmd == "G28" and no axes specified:
    emit home XY
    emit home Z
```

Alternatywa mniej idealna, ale bezpieczniejsza niż `0x7F`:

```text
03 05 07 ...
```

czyli tylko X/Y/Z, bez E/A/B/Z2.

Jednak preferowana poprawka to **rozdzielone XY potem Z**, bo taki układ odpowiada referencji Z-Suite.

---

## 13. Bezpieczna interpretacja objawu użytkownika

Objaw:

```text
drukarka robi tylko X/Y i zaczyna grzać, bez Z-home
```

może oznaczać jedną z trzech sytuacji:

1. w pliku nie ma `;ZORTRAX_START_MACHINE AUTO`,
2. zwykły `G28` jest konwertowany do `03 05 7f 61`, co nie odpowiada dokładnie Z-Suite,
3. Z-home nie został jawnie wygenerowany jako `03 05 04 89`.

Najważniejsze: jeśli w pliku wynikowym nie ma `03 05 04 89`, to konwerter nie wygenerował jawnego, referencyjnego homingu Z.

---

## 14. Co sprawdzać w kolejnych testach

Przy każdym testowym `.zcode` trzeba zdekodować początek strumienia i szukać:

```text
03 05 03 dd   ; home X/Y
03 05 04 89   ; home Z
```

Jeżeli występuje tylko:

```text
03 05 03 dd
```

to jest tylko home X/Y.

Jeżeli występuje:

```text
03 05 7f 61
```

to prawdopodobnie pochodzi ze zwykłego `G28` bez parametrów i wymaga poprawki.

Jeżeli występuje para:

```text
03 05 03 dd
03 05 04 89
```

to start ma referencyjny homing X/Y + Z.

---

## 15. Status obecny

### Potwierdzone

- Marker `;ZORTRAX_START_MACHINE AUTO` generuje Z-Suite-like start z home X/Y i home Z.
- Zwykłe `G28 X0 Y0` generuje `03 05 03 dd`.
- Zwykłe `G28 Z0` generuje `03 05 04 89`.
- Zwykłe `G28` bez parametrów generuje obecnie `03 05 7f 61`.
- Przykładowy realny plik bez właściwego markera może nie mieć jawnego `03 05 04 89`.

### Otwarte / do poprawy

- poprawić obsługę gołego `G28`,
- zdecydować, czy `G28` ma emitować:
  - rozdzielone `XY` + `Z`, preferowane,
  - czy jeden payload `0x07`,
- ewentualnie dodać kontrolę bezpieczeństwa:
  - jeśli przed pierwszym ruchem drukującym nie było `home Z`, konwerter automatycznie wstawia `03 05 04 89`.

---

## 16. Najkrótszy prompt do nowego chatu

Można wkleić w nowym chacie:

> Kontynuujemy projekt Zortrax Inventure / Orca / pure Python `.zcode`.
>
> Najnowszy konwerter to `g2z_wrapper_orca.py` v1.07-full-orca-placeholders.
>
> W tym wątku sprawdzono firmware’owe procedury kalibracji i homing:
>
> - Nie znaleziono potwierdzonego sposobu wywołania `Nozzle Alignment Calibration` ani `Platform Leveling` z G-code / `.zcode`.
> - Te procedury są interaktywne i uruchamiane z menu drukarki.
> - Można zrobić własny pre-print alignment check, ale nie zapisze on offsetu w firmware.
> - Marker `;ZORTRAX_START_MACHINE AUTO` generuje poprawny Z-Suite-like homing:
>   - `03 05 03 dd` = home X/Y
>   - `03 05 04 89` = home Z
> - Zwykły `G28 X0 Y0` daje `03 05 03 dd`.
> - Zwykły `G28 Z0` daje `03 05 04 89`.
> - Problem: zwykły `G28` bez parametrów daje obecnie `03 05 7f 61`, bo konwerter ustawia bitfield dla X/Y/Z/E/A/B/Z2.
> - Zalecana poprawka: `G28` bez parametrów powinno emitować jak Z-Suite:
>   - `03 05 03 dd`
>   - `03 05 04 89`
> - W Orca w Machine start G-code należy używać:
>   - `;ZORTRAX_START_MACHINE AUTO`
> - Tool change:
>   - `;ZORTRAX_SPECIAL_CLEAN AUTO`
> - End:
>   - `;ZORTRAX_END_MACHINE AUTO`
>
> Następny krok: poprawić obsługę gołego `G28` w konwerterze i przetestować, czy wynikowy `.zcode` zawsze zawiera jawny home Z przed pierwszym ruchem drukującym.

---

## 17. Minimalne streszczenie

- Brak znanej komendy do firmware `Nozzle Alignment Calibration`.
- Brak znanej komendy do firmware `Platform Leveling`.
- Obie procedury są interaktywne z menu drukarki.
- Pre-print wzorzec kontrolny jest możliwy, ale nie zapisuje kalibracji.
- `;ZORTRAX_START_MACHINE AUTO` działa dobrze i zawiera:
  - home X/Y = `03 05 03 dd`,
  - home Z = `03 05 04 89`.
- Zwykły `G28` ma błąd mapowania: generuje `03 05 7f 61`.
- Trzeba poprawić `G28` bez parametrów na rozdzielone XY + Z.


## A26. `Zortrax_Inventure_Project_Summary.md`

# Zortrax Inventure + OrcaSlicer Integration — Projekt Podsumowanie

## 1. Cel projektu
Celem projektu było umożliwienie pełnej obsługi drukarki **Zortrax Inventure** z poziomu **Orca Slicer**, z zachowaniem kompatybilności z formatem `.zcode` oraz logiką działania Z-Suite.

Projekt obejmuje:
- konwerter G-code → ZCode (pure Python),
- konfiguracje Orca (dual i single),
- mapowanie metadanych Orca → Zortrax,
- implementację procedur czyszczenia, purge i toolchange.

---

## 2. Architektura rozwiązania

### 2.1 Pipeline
1. Orca generuje G-code + ORCA METADATA
2. Skrypt post-process uruchamia konwerter
3. Konwerter:
   - parsuje metadata,
   - interpretuje markery `ZORTRAX_*`,
   - generuje ZCode (binary),
   - patchuje nagłówek Inventure

---

## 3. Kluczowe markery G-code

### ZORTRAX_START_MACHINE
```
;ZORTRAX_START_MACHINE AUTO
```
- wykonuje homing XY + Z
- ustawia temperatury (bed, chamber, nozzle)
- wybiera tryb single/dual
- ustawia pozycję startową (drop zone)

---

### ZORTRAX_START_PURGE
```
;ZORTRAX_START_PURGE AUTO LENGTH=60 RETRACT=5
```
- działa w drop zone
- SINGLE:
  - purge T0
- DUAL:
  - purge T0 i T1
- używa:
  - deretraction_speed → prędkość purge
  - retraction_speed → prędkość cofania
  - nozzle_temperature_initial_layer

---

### ZORTRAX_SPECIAL_CLEAN
```
;ZORTRAX_SPECIAL_CLEAN AUTO 5 PURGE=AUTO IDLE_RETRACT=AUTO
```
- czyszczenie co N warstw
- używa danych z `ZORTRAX_TOOLCHANGE_META`
- wykonuje:
  - retract starego extrudera
  - purge nowego
  - sekwencję czyszczenia Zortrax

---

### ZORTRAX_TOOLCHANGE_META
Zawiera dane Orca:
- previous_extruder / next_extruder
- layer_num
- flush_length
- retraction lengths
- extrusion speeds

---

## 4. Metadane Orca wykorzystywane przez konwerter

### Ruch i prędkości
- travel_speed
- retraction_speed
- deretraction_speed

### Temperatury
- nozzle_temperature_initial_layer
- nozzle_temperature
- chamber_temperature

### Materiały
- filament_t0 / filament_t1
- filament_type

### Stół roboczy
- curr_bed_type
- bed_temp_* (dynamiczny wybór)

---

## 5. Logika single vs dual

### Dual
- używa T0 + T1
- pełna obsługa supportu
- toolchange aktywny

### Single
- tylko T0
- brak T1 w machine i file header
- process i filamenty zachowane z dual

---

## 6. Najważniejsze ustalenia projektowe

### ✔ zachowanie procesów i filamentów
- konfiguracja single tworzona z dual
- NIE zmieniamy process ani filament

### ✔ brak twardych wartości
- prędkości pobierane z metadanych Orca

### ✔ drop zone
- wymuszany przez konwerter
- niezależny od pozycji

### ✔ kompatybilność
- Orca 2.3.x / 2.4.x
- macOS / Windows

---

## 7. Znane ograniczenia

### PURGE=AUTO
- jeśli `flush_length = 0` → brak purge
- zależne od Orca

### mechanika Inventure
- jeden napęd → możliwe kapanie
- wymaga retrakcji przy toolchange

---

## 8. Rekomendacje

### Start G-code
```
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE AUTO LENGTH=30 RETRACT=5
```

### Toolchange
```
;ZORTRAX_SPECIAL_CLEAN AUTO 5 PURGE=AUTO IDLE_RETRACT=AUTO
```

---

## 9. Stan projektu

### ✔ stabilne
- konwersja G-code → ZCode
- start machine
- start purge
- dual/single config

### ⚠️ rozwój
- dynamic purge (Orca flush logic)
- optymalizacja ooze
- lepsza kontrola materiału support

---

## 10. Wersja produkcyjna
FINAL_PRODUCTION_v1.0

---

## 11. Podsumowanie

Projekt osiągnął pełną funkcjonalność:
- Orca → Inventure bez Z-Suite
- zachowanie jakości druku
- pełna kontrola nad startem i toolchange

Dalsze prace to głównie optymalizacja, nie stabilność.


## A27. `ZORTRAX_INVENTURE_transfer_2026-04-15.md`

# ZORTRAX INVENTURE — transfer summary for new chats

This file is a compact but practical transfer note for continuing work in another chat without rebuilding context from zero.

---

## 1. Main project scope

The project combines four connected areas:

1. **OrcaSlicer presets and bundles** for **Zortrax Inventure 0.4 nozzle**.
2. **Conversion pipeline**: `Orca -> G-code -> g2z.jar -> patched .zcode`.
3. **Header patching for classic Inventure `.zcode`**.
4. **Printer-specific behavior**, especially materials, supports, tool changes, cleaning routines, and platform-specific launchers.

Preferred working style:
- practical, test-ready changes,
- consistent naming,
- minimal unnecessary edits,
- preserve bundle integrity,
- do not draw conclusions from mismatched comparison files.

---

## 2. Confirmed `.zcode` header fields for Inventure

Treat these offsets as confirmed working assumptions:

- `54..57` — print time
- `61` — printer id
- `62` — model material
- `63` — layer
- `64` — quality
- `65` — infill
- `66` — support angle / support parameter used by Z-Suite
- `68..71` — Z-Suite / software version
- `73..74` — model filament length
- `77..78` — support filament length
- `85` — support material
- `127` — header CRC

Also treated as practically confirmed:
- `58..60` — job mode / compatibility / firmware triplet

---

## 3. Confirmed logic for bytes `58..60`

These are **not** material codes.
They behave like a **job mode / compatibility triplet**.

Confirmed working rules:

- **single-material** -> `01 02 01`
- **dual + BASF Ultrafuse BVOH** -> `01 02 01`
- **dual + Z-SUPPORT** -> `01 03 00`
- **dual + Z-SUPPORT Plus** -> `01 03 00`
- **dual + Z-SUPPORT Premium** -> `01 03 00`

Practical rule:
- Z-SUPPORT family uses `01 03 00`
- BASF BVOH and single-material jobs use `01 02 01`

---

## 4. Confirmed material mapping

### Native Zortrax materials

- `Z-ULTRAT` -> `0x01`
- `Z-GLASS` -> `0x02`
- `Z-HIPS` -> `0x03`
- `Z-PCABS` -> `0x04`
- `Z-PETG` -> `0x05`
- `Z-ULTRAT PLUS` -> `0x06`
- `Z-SUPPORT` -> `0x07`
- `Z-ESD` -> `0x08`
- `Z-PHA` -> `0x09`
- `Z-PLA` -> `0x0A`
- `Z-PLA PRO` -> `0x0B`
- `Z-ASA PRO` -> `0x0C`
- `Z-SUPPORT PLUS` -> `0x0D`
- `Z-SEMIFLEX` -> `0x0E`
- `Z-FLEX` -> `0x0F`
- `Z-NYLON` -> `0x10`
- `Z-SUPPORT PREMIUM` -> `0x11`
- `Z-PEEK` -> `0x12`

### External / open materials

- `ABS-BASED FILAMENT` -> `0x81`
- `GLASS-TYPE FILAMENT` -> `0x84`
- `FLEX-BASED FILAMENT` -> `0x85`
- `PLA-BASED FILAMENT` -> `0x86`
- `PETG-BASED FILAMENT` -> `0x87`
- `NYLON-BASED FILAMENT` -> `0x89`
- `ULTRAT-BASED FILAMENT` -> `0x91`
- `ESD PETG-BASED FILAMENT` -> `0x92`
- `PLA PRO-BASED FILAMENT` -> `0x94`
- `ASA PRO-BASED FILAMENT` -> `0x95`
- `SEMIFLEX-BASED FILAMENT` -> `0x96`

### BASF support

Use as confirmed working mapping:

- `BASF ULTRAFUSE BVOH` -> `0x17`

Aliases like `BVOH`, `ULTRAFUSE BVOH`, `BASF BVOH` should map to `0x17`.

---

## 5. CRC status

CRC logic is treated as confirmed.

- CRC algorithm is correct.
- Byte `127` is recalculated correctly.
- CRC matches reference `.zcode` files from Z-Suite.

Practical consequence:
If the printer reports a material-related error, the first suspects are usually:
- `62`
- `85`
- `58..60`
- model/support material relationship

not CRC itself.

---

## 6. Active patcher logic

Core patcher behavior should be:

1. read Orca G-code,
2. read `ORCA METADATA`,
3. read fallbacks from comments if needed,
4. determine:
   - `model_code`
   - `support_code`
   - `single_material`
   - `support_length_mm`
   - `model_length_mm`
   - `quality`
5. run `g2z.jar` or patch an already converted file,
6. patch confirmed header fields,
7. recalculate CRC.

### Single-material rule

Treat a job as single if:
- `support_length_mm == 0`, or
- support is effectively absent / same as model without real support usage.

Then:
- `support_code = model_code`
- `support_length_mm = 0`
- `58..60 = 01 02 01`

### Support triplet rule

Use:
- `01 03 00` when real support exists and support material is in Z-SUPPORT family (`0x07`, `0x0D`, `0x11`)
- `01 02 01` for everything else

---

## 7. Preferred Orca bundle structure

Preferred final organization:

- **1 `.orca_printer` bundle**
- **2 printers**:
  - `Zortrax Inventure 0.4 nozzle - single`
  - `Zortrax Inventure 0.4 nozzle - dual`
- **8 processes total**:
  - 4 for `single`
  - 4 for `dual`
- shared filament presets

Default presets to preserve:

### Dual
- `default_print_profile = "0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual"`
- `default_filament_profile = ["Z-PLA", "Z-SUPPORT"]`

### Single
- `default_print_profile = "0.15mm Quality @Zortrax Inventure 0.4 nozzle - single"`
- `default_filament_profile = ["Z-PLA"]`

---

## 8. Critical Orca bundle rules

When editing `.orca_printer` bundles:

- preserve ZIP integrity,
- preserve JSON validity,
- keep `bundle_structure.json` consistent,
- avoid orphan references,
- keep names, IDs, filenames and references aligned.

When renaming a preset, update together:
- `name`
- related `*_settings_id`
- JSON filename
- `bundle_structure.json`
- `compatible_printers` references if applicable

When merging presets:
- copy only technology/behavior fields,
- do **not** copy identity fields like:
  - `name`
  - `inherits`
  - `print_settings_id`

When creating a thinner layer-height preset, remember printer constraints too.
Example already established earlier:
- for `0.08mm Ultra Quality`, `min_layer_height` had to be reduced from `0.15` to `0.08`.

---

## 9. Established Orca conclusions from earlier bundle work

These are already established and should not be rediscovered from scratch:

- Export issues for Orca process presets were likely due to Orca behavior / limitations rather than broken ZIP/JSON bundle structure.
- If exporting a process fails, practical workaround is:
  1. import the bundle,
  2. do `Save As` in Orca,
  3. export from that saved local preset.
- `External PEEK @INVENTURE -> External PEEK` required coordinated renaming across the whole bundle.

---

## 10. macOS Sequoia launcher conclusion

Key finding:
- Orca GUI on macOS may launch post-processing scripts with a very minimal `PATH`.
- This can cause the script to resolve `/usr/bin/java` (Apple stub) instead of a real Java runtime.

Therefore macOS launchers must:
1. check Homebrew Java paths first,
2. validate them with `java -version`,
3. reject stub Java,
4. only then fall back to generic PATH lookup.

Important naming rule:
Keep stable filenames and do not create unnecessary parallel variants.

---

## 11. Recent G-code / extruder mode findings from this chat

These points were clarified in the latest conversation and should be preserved:

### Extruder mode commands

- `M83` = **relative extrusion mode**
- `M82` = **absolute extrusion mode**
- `M92` = **steps per unit**, not extrusion mode

### Example interpretation

Given:

```gcode
G90
M83
G1 X0 Y20 E6 F350
```

this means:
- `G90` -> X/Y/Z absolute positioning
- `M83` -> E is relative
- `G1 X0 Y20 E6 F350` -> move to absolute `X0 Y20` while extruding **+6 mm** of filament at **350 mm/min**

Important practical note:
- with `M83`, every `E6` means **another +6 mm**, not a persistent target position.

---

## 12. Recent toolchange / cleaning conclusion from this chat

### Goal

The user wants the printer to clean **the nozzle that will be used next**, not the nozzle that was active before toolchange.

### Core logic

The cleaning sequence must happen in the **toolchange / change filament context**, not as a normal layer-change-only sequence.

Desired order is:
1. finish buffered moves,
2. switch to the next tool,
3. wait for the newly selected nozzle to reach temperature,
4. move to the cleaning area,
5. perform the wipe passes.

### Important caution

In this conversation the Orca placeholder/parser behavior was inconsistent.
There was already a syntax problem in the user's screenshot when trying to force tool selection via placeholder.

Therefore the **logic is clear**, but the **exact placeholder syntax must be verified in the user's Orca build by slicing a tiny dual-material test and reading the generated G-code**.

Do **not** assume without verification that every one of the following will parse in the current environment:
- `{next_extruder}`
- `[next_extruder]`
- `new_filament_temp`
- mixed placeholder styles in one field

### Working target sequence for toolchange cleaning

Use this as the **behavioral template**, then adapt syntax to whatever the slicer parser accepts:

```gcode
; ===== Filament change cleaning procedure =====
; Switch to the next tool first, then clean the nozzle that will actually be used

M400                                    ; Wait for all buffered moves to finish
T<next tool>                            ; Activate the next extruder/tool before cleaning
M109 S<new tool temperature>            ; Wait until the newly selected nozzle reaches target temperature
G90                                     ; Use absolute positioning mode
G1 X67 Y140 F6000                       ; Move to filament change entry position / cleaning area approach
G1 X52 Y140 F3000                       ; Move to cleaning start position 1
G1 X52 Y155 F3000                       ; Cleaning pass 1 along Y axis
G1 X52 Y140 F3000                       ; Return after cleaning pass 1
G1 X56 Y140 F3000                       ; Move to cleaning start position 2
G1 X56 Y155 F3000                       ; Cleaning pass 2 along Y axis
G1 X56 Y140 F3000                       ; Return after cleaning pass 2
G1 X60 Y140 F3000                       ; Move to cleaning start position 3
G1 X60 Y155 F3000                       ; Cleaning pass 3 along Y axis
G1 X60 Y140 F3000                       ; Return after cleaning pass 3
G1 X64 Y140 F3000                       ; Move to cleaning start position 4
G1 X64 Y155 F3000                       ; Cleaning pass 4 along Y axis
G1 X64 Y140 F3000                       ; Return after cleaning pass 4
G1 X68 Y140 F3000                       ; Move to cleaning start position 5
G1 X68 Y155 F3000                       ; Cleaning pass 5 along Y axis
G1 X68 Y140 F3000                       ; Return after cleaning pass 5
G1 X72 Y140 F3000                       ; Move to cleaning start position 6
G1 X72 Y155 F3000                       ; Cleaning pass 6 along Y axis
G1 X72 Y140 F3000                       ; Return after cleaning pass 6
G1 X77 Y140 F3000                       ; Move to cleaning start position 7
G1 X77 Y155 F3000                       ; Cleaning pass 7 along Y axis
G1 X77 Y140 F3000                       ; Return after cleaning pass 7
G1 X82 Y140 F3000                       ; Move to cleaning start position 8
G1 X82 Y155 F3000                       ; Cleaning pass 8 along Y axis
G1 X82 Y140 F3000                       ; Return after cleaning pass 8
```

### What must be checked next in a new chat

1. Which exact Orca field is being used:
   - `Change filament G-code`
   - `Tool change G-code`
   - `Layer change G-code`
2. Which placeholders are actually accepted in that field by the installed Orca version.
3. Whether Orca itself inserts another `T0/T1` later, causing double toolchange.
4. Whether the generated G-code order really becomes:
   - `T...`
   - `M109 ...`
   - cleaning moves

### Practical rule

Do not trust only the UI text box.
Always inspect the generated G-code around the first real material/tool change.

---

## 13. Open issues that remain unresolved

Still open:
- full meaning of all undocumented header bytes outside the confirmed set,
- full meaning of constant `225` in firmware update files,
- unpacking/decrypting firmware payloads,
- full command set for Inventure firmware,
- all cases where the printer still reports material errors despite correct CRC,
- final verified placeholder syntax for forced tool-before-cleaning logic in the user's Orca environment.

---

## 14. Safe working rules for future chats

1. Do not compare non-equivalent files and then infer header meaning from that.
2. First suspect `62`, `85`, `58..60`, and material relationships before suspecting CRC.
3. Keep `.orca_printer` bundles structurally consistent at all times.
4. For `single`, remove leftover dual support filament assignments.
5. Preserve stable filenames in scripts and launchers.
6. For toolchange cleaning, verify parser output in generated G-code before trusting placeholder syntax.

---

## 15. Suggested starter prompt for a new chat

You can paste this into a fresh chat:

> We are continuing work on Zortrax Inventure.
>
> Keep this context:
> - confirmed `.zcode` header offsets: 54..57, 61, 62, 63, 64, 65, 66, 68..71, 73..74, 77..78, 85, 127
> - bytes 58..60 are a job mode / compatibility triplet:
>   - single and BASF BVOH -> `01 02 01`
>   - Z-SUPPORT / Z-SUPPORT Plus / Z-SUPPORT Premium -> `01 03 00`
> - BASF Ultrafuse BVOH = `0x17`
> - CRC is correct and should not be treated as the primary problem source
> - preferred Orca organization is 1 bundle with 2 printers (`single`, `dual`), 8 processes, and shared filaments
> - on macOS, Orca GUI may pick `/usr/bin/java` stub; launcher must detect real Java
> - recent goal: make nozzle cleaning happen **after selecting the next tool**, so the nozzle that will continue printing is the one being cleaned
> - recent caution: the exact Orca placeholder syntax for forcing next-tool selection must be verified by inspecting generated G-code in the current Orca build
>
> Continue from this state.

---

## 16. Shortest possible transfer version

- `.zcode` fields confirmed: 54..57, 61, 62, 63, 64, 65, 66, 68..71, 73..74, 77..78, 85, 127
- `58..60`:
  - single + BASF BVOH -> `01 02 01`
  - Z-SUPPORT family -> `01 03 00`
- `BASF Ultrafuse BVOH = 0x17`
- CRC is correct
- preferred Orca bundle: 2 printers, 8 processes, shared filaments
- for toolchange cleaning: switch tool first, heat selected nozzle, then wipe
- exact placeholder syntax in Orca still needs verification in generated G-code



## A28. `ZORTRAX_INVENTURE_transfer_summary_2026-04-15.md`

# ZORTRAX INVENTURE — pełne podsumowanie rozmowy do transferu do źródeł

Data podsumowania: 2026-04-15  
Zakres: Orca Slicer -> G-code -> g2z.jar -> patcher/wrapper -> `.zcode` dla Zortrax Inventure, ze szczególnym naciskiem na problem `Use relative E distances`, `G92 E0`, brim/prime tower oraz finalną logikę `g2z_wrapper_orca.py`.

---

## 1. Najważniejszy wynik tej rozmowy

Ustalono praktycznie i testowo, że dla workflow:

**Orca -> G-code -> g2z.jar -> patcher -> Inventure**

problem z ekstruzją nie wynikał z samego nagłówka `.zcode`, tylko z tego, jak `g2z.jar` / dalszy pipeline reaguje na G-code generowany z:

- `Use relative E distances = ON`
- `M83`
- dodatkowe `G92 E0` w `layer change G-code`

Najważniejszy wynik:

- sam plik G-code z Orca przy `M83` wygląda logicznie poprawnie,
- ale po konwersji przez `g2z.jar` drukarka zachowuje się niepoprawnie,
- testy wykazały, że skuteczniejsze jest **tymczasowe przekształcenie regionu druku z `M83` na styl Orca `M82`**, a dopiero potem uruchomienie `g2z.jar`.

To doprowadziło do finalnej logiki wrappera:

- jeśli wejście jest już w `M82` / absolute E -> iść starą ścieżką,
- jeśli wejście jest w `M83` / relative E -> na kopii roboczej przekształcić region druku do stylu `M82`, zachowując wartości z G-code, a dopiero potem wykonać `g2z.jar` i patch nagłówka.

---

## 2. Diagnoza problemu `Use relative E distances`

### Objawy początkowe

W pliku z włączonym `Use relative E distances` oraz `G92 E0` w `layer change G-code` drukarka zaczynała „szaloną ekstruzję” już na pierwszym brimie.

Wstępny trop był taki, że problemem może być zapis typu:

- `E.10335`
- `E.06797`

czyli brak zera wiodącego przed częścią dziesiętną.

### Co wykazała analiza G-code

Porównanie dwóch plików pokazało:

- działający wariant używał w części drukującej **`M82`**,
- problematyczny wariant używał **`M83`**,
- sam G-code przy `M83` miał logicznie poprawne małe przyrosty `E`, np. `E0.10335`, `E0.06797`, `E1.61982`, więc źródło błędu nie wyglądało na prostą pomyłkę slicera.

Wniosek roboczy:

- `g2z.jar` prawdopodobnie nie interpretuje poprawnie `M83` w tym workflow,
- albo niepoprawnie obsługuje małe przyrosty `E`,
- albo źle reaguje na kombinację `M83` + `G92 E0` + dalsza konwersja.

---

## 3. Test z „zerem wiodącym”

Przygotowano i zintegrowano skrypt normalizujący liczby typu:

- `E.123 -> E0.123`
- `X-.5 -> X-0.5`

Następnie wpięto tę logikę do wrappera tak, aby na kopii roboczej G-code następowała normalizacja przed `g2z.jar`.

### Wynik testu

Po tej zmianie drukarka nie przechodziła już w nadmierną ekstruzję, ale **ekstrudery przestały podawać materiał**.

Wniosek:

- samo zero wiodące nie jest docelowym rozwiązaniem problemu,
- test potwierdził raczej, że sednem problemu jest **relative E (`M83`)**, a nie sam format liczb.

---

## 4. Testy konwersji `M83 -> M82`

### 4.1. Pierwsza próba: prosta konwersja do `M82`

Wykonano test polegający na przeliczeniu wartości ekstruzji z trybu względnego na absolutny i zamianie `M83` na `M82`.

### Wynik

Pierwsza wersja nie zadziałała poprawnie, bo logika resetów `G92 E0` nie odpowiadała temu, jak Orca zapisuje działający G-code w absolute mode.

### 4.2. Druga próba: styl „Orca-like M82”

W kolejnej wersji odtworzono układ zgodny z działającym plikiem Orcy:

- `M82`
- `G92 E0`
- retract
- `G92 E0`
- unretract
- dalsze absolutne `E`

### Wynik

Ten test był przełomowy:

- **teraz było OK**,
- drukarka zaczęła działać poprawnie,
- potwierdziło to, że samo przejście na styl `M82` ma sens, ale ważna jest też forma resetów `G92 E0`.

---

## 5. Test bez `G92 E0` po przeliczonych retrakcjach

Na życzenie wykonano dodatkowy test, w którym wrapper podczas konwersji `M83 -> M82` **nie dodawał `G92 E0` po retrakcjach**.

### Wynik fizyczny wydruku

Użytkownik zgłosił bardzo istotny objaw:

- **prime line wydrukował się**,
- **brim się nie wydrukował**,
- **prime tower wydrukował się**.

### Interpretacja

To wskazało, że:

- ekstruder i materiał działają,
- nie ma ogólnego braku ekstruzji,
- problem dotyczy bardzo konkretnego fragmentu logiki zaraz po wejściu w właściwy obszar drukowania,
- bez dodatkowego `G92 E0` po przeliczonej retrakcji pierwszy brim/skirt może zaczynać się od niekorzystnego stanu licznika `E`.

Wniosek końcowy:

- w ścieżce konwersji `M83 -> M82` **należy zostawić `G92 E0` tam, gdzie trzeba po przeliczonych retrakcjach**,
- samo `G92 E0` w `layer change G-code` Orcy **nie zastępuje** tej logiki.

---

## 6. Ostateczne rozróżnienie: co dzieje się w oryginalnym G-code, a co w wrapperze

Bardzo ważne ustalenie metodologiczne:

### W oryginalnym G-code z Orca przy `M83`

- `M83` ustawia relative E,
- `G92 E0` w `layer change G-code` może zostać, jeśli użytkownik go potrzebuje,
- ale relative mode **nie wymaga** sam z siebie `G92 E0` po każdej retrakcji.

### W kopii roboczej generowanej przez wrapper przy konwersji `M83 -> M82`

- wrapper może i powinien dodawać `G92 E0` po przeliczonych retrakcjach, jeśli to jest konieczne do zachowania stylu działającego pliku Orcy i poprawnej interpretacji przez `g2z.jar` / Inventure.

Czyli:

- użytkownik **nie musi** ręcznie dopisywać `G92 E0` po każdej retrakcji w Orca,
- ale **wrapper może to robić na kopii roboczej**, jeśli konwertuje `M83` do `M82`.

---

## 7. Finalna logika wrappera `g2z_wrapper_orca.py`

### Ustalona wersja finalna

Finalna wersja wrappera ma zachowywać dotychczasowy interfejs dla launcherów Orca i działać automatycznie zależnie od typu ekstruzji.

### 7.1. Gdy wejściowy G-code jest już w `M82` / absolute E

Wrapper ma iść starą, prostą ścieżką:

1. przygotować kopię roboczą G-code,
2. znormalizować liczby typu `E.123 -> E0.123` i `X-.5 -> X-0.5`,
3. uruchomić `g2z.jar`,
4. patchować nagłówek `.zcode`,
5. przeliczyć CRC,
6. wypisać raport z wartościami i źródłami danych.

### 7.2. Gdy wejściowy G-code jest w `M83` / relative E

Wrapper ma:

1. wykryć relative E,
2. przetworzyć region drukowania na kopii roboczej,
3. zamienić go do stylu **Orca-like `M82`**,
4. zachować rzeczywiste wartości wynikające z G-code:
   - ekstruzja,
   - retrakcja,
   - unretrakcja,
5. **zostawić `G92 E0` tam, gdzie trzeba po przeliczonych retrakcjach**, zgodnie z działającym testem,
6. dopiero potem uruchomić `g2z.jar`,
7. patchować nagłówek `.zcode`,
8. przeliczyć CRC,
9. wypisać raport końcowy.

### 7.3. Zachowany interfejs CLI

Wrapper musi nadal być zgodny z launcherami i przyjmować:

- wejściowy plik G-code jako pierwszy argument,
- `--java`
- `--jar`
- `--out-dir`
- `--log`

Dzięki temu istniejące skrypty `.bat`, `.command`, `.sh` nie wymagają zmian.

---

## 8. Raport źródeł danych patchowanych pól

Wrapper został rozszerzony tak, aby dla każdego patchowanego pola pokazywać nie tylko wartość, ale też źródło tej wartości.

### Raport obejmuje:

- `model`
- `support`
- `layer`
- `quality`
- `infill`
- `support_angle`
- `print_time`
- `model_mm`
- `support_mm`
- `single_material`
- `fw_triplet`
- `device_id`
- `software_version`
- `header_crc`

### Przykładowe źródła

- `ORCA_METADATA:model`
- `ORCA_METADATA:infill`
- `comment:print_time`
- `comment:model_mm`
- `derived:quality_from_layer`
- `derived:single_material_support_equals_model`

To było potrzebne, żeby łatwo diagnozować, z którego pola G-code / komentarza / metadanych dana wartość trafiła do nagłówka `.zcode`.

---

## 9. Ustalenie dotyczące pola `infill`

Ustalono konkretnie, skąd wrapper bierze `infill`.

### Kolejność źródeł:

1. najpierw z bloku `ORCA METADATA`:
   - `infill_density=...`
2. jeśli brak, to fallback z komentarza:
   - `; sparse_infill_density = ...`
3. wynik trafia do nagłówka `.zcode` na offset `65`.

Przykład z analizowanego pliku:

- `; infill_density=30` w ORCA METADATA było głównym źródłem,
- `; sparse_infill_density = 30%` było tylko fallbackiem.

---

## 10. Zgodność launcherów `.bat`, `.command`, `.sh`

Użytkownik ma osobne launchery zależnie od systemu.

### Wniosek z analizy launcherów

- skrypty wywołujące są kompatybilne z finalną wersją wrappera,
- ponieważ wszystkie one odwołują się do pliku:
  - `g2z_wrapper_orca.py`
- i przekazują zgodne argumenty CLI.

### Ważne rozróżnienie

Mogą leżeć obok siebie dwa pliki:

- `g2z_wrapper_orca.py`
- `g2z_wrapper_orca_integrated.py`

ale launchery i tak uruchamiają tylko:

- `g2z_wrapper_orca.py`

Wniosek praktyczny:

- jako plik docelowy do katalogów `OrcaScripts` / katalogu macOS należy traktować **`g2z_wrapper_orca.py`**,
- drugi plik może leżeć obok, ale nie bierze udziału w pracy, dopóki launchery nie zostaną na niego przełączone.

---

## 11. Najważniejsze pliki wygenerowane / użyte w tej rozmowie

### Wrappery i skrypty

- `g2z_wrapper_orca.py` — finalny wrapper do użycia przez Orca
- `g2z_wrapper_orca_integrated.py` — plik pomocniczy / równoległy
- `normalize_leading_zero_gcode.py` — wcześniejszy osobny skrypt testowy
- `run_g2z_orca_postprocess.bat`
- `run_g2z_orca_postprocess.command`
- `run_g2z_orca_postprocess.sh`
- `g2z.jar`

### Testowe pliki G-code / Z-code

- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.leading_zero_normalized.gcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.leading_zero_test.zcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.m82_converted_test.gcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.m82_converted_test.zcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.m82_orca_style_test.gcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.m82_orca_style_test.zcode`
- `20p_scale_erdinger_v1_0.15_Z-ULTRAT Plus_Z-HIPS_8h14m.no_g92_after_retract_test.gcode`
- `20p_scale_erdinger_v1_0.15_Z-ULTRAT Plus_Z-HIPS_8h14m.no_g92_after_retract_test.zcode`

### Pliki wejściowe użytkownika analizowane w tej rozmowie

- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m.gcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m.zcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.gcode`
- `20p_scale_erdinger_v1_0.3_Z-ULTRAT Plus_Z-HIPS_4h9m 2.zcode`
- `20p_scale_erdinger_v1_0.15_Z-ULTRAT Plus_Z-HIPS_8h14m.gcode`

---

## 12. Aktualny stan wiedzy po tej rozmowie

### Potwierdzone praktycznie

1. Problem nadekstruzji / braku ekstruzji jest silnie związany z `M83` / relative E w pipeline z `g2z.jar`.
2. Samo dodanie zera wiodącego nie rozwiązuje problemu.
3. Skuteczne obejście to automatyczna konwersja regionu druku `M83 -> Orca-like M82` na kopii roboczej.
4. W tej konwersji trzeba zostawić `G92 E0` tam, gdzie wynika to z przeliczonych retrakcji.
5. `G92 E0` w `layer change G-code` użytkownika może zostać, ale nie zastępuje logiki wrappera.
6. Finalny wrapper ma zachować pełną zgodność z launcherami `.bat/.command/.sh`.
7. Raport patchowanych pól z ich źródłami jest bardzo przydatny diagnostycznie i ma pozostać w finalnej wersji wrappera.

### Nadal otwarte / nie do końca rozpoznane

1. pełna semantyka wszystkich nieudokumentowanych bajtów nagłówka `.zcode` poza już potwierdzonymi offsetami,
2. pełne zachowanie `g2z.jar` dla wszystkich wariantów G-code,
3. pełna zgodność mapowania materiałów external w aktualnym kodzie z wcześniejszą dokumentacją projektu,
4. kompletne mapowanie `quality` dla wszystkich wysokości warstwy,
5. głębsza analiza firmware payloadu `InventureUpdate.bin`.

---

## 13. Finalna rekomendacja operacyjna

### Dla użytkowania Orca

- zachować obecne launchery systemowe,
- jako docelowy wrapper używać:
  - `g2z_wrapper_orca.py`
- pozostawić `G92 E0` w `layer change G-code`, jeśli jest potrzebne użytkownikowi do konfiguracji Orcy przy relative mode,
- nie dopisywać ręcznie `G92 E0` po każdej retrakcji w samym Orca,
- pozwolić wrapperowi wykonać wewnętrzną konwersję tylko wtedy, gdy wejście rzeczywiście jest w `M83`.

### Dla kodu projektu

Finalna, preferowana logika powinna pozostać taka:

- `relative OFF` -> stara ścieżka,
- `relative ON` -> konwersja regionu druku do Orca-like `M82` z zachowaniem `G92 E0` po przeliczonych retrakcjach -> `g2z.jar` -> patch nagłówka.

---

## 14. Krótki prompt do nowego chatu

Można wkleić na start nowej rozmowy:

> Pracujemy nad Zortrax Inventure i finalnym wrapperem `g2z_wrapper_orca.py` dla workflow Orca -> G-code -> g2z.jar -> patcher -> `.zcode`.
>
> Najważniejsze ustalenia z poprzedniej rozmowy:
> - problem dotyczył głównie `Use relative E distances` / `M83` w pipeline z `g2z.jar`,
> - samo dodanie zera wiodącego nie naprawia problemu,
> - skuteczne obejście to konwersja regionu druku `M83 -> Orca-like M82` na kopii roboczej,
> - w tej konwersji trzeba zachować `G92 E0` tam, gdzie wynika to z przeliczonych retrakcji,
> - `G92 E0` w `layer change G-code` użytkownika może zostać, ale nie zastępuje logiki wrappera,
> - finalny `g2z_wrapper_orca.py` ma auto-wykrywać `M82/M83`,
> - dla `M82` używa starej ścieżki, dla `M83` robi konwersję do stylu `M82`, potem `g2z.jar` i patch,
> - wrapper ma raportować źródła patchowanych pól (`model`, `support`, `layer`, `quality`, `infill`, `support_angle`, `print_time`, `model_mm`, `support_mm`, itd.),
> - launchery `.bat`, `.command`, `.sh` są kompatybilne z finalnym wrapperem, bo odwołują się do `g2z_wrapper_orca.py`.

---

## 15. Najkrótsze streszczenie

Jeśli trzeba zachować tylko absolutne minimum:

- `M83` w pipeline z `g2z.jar` powoduje błędy ekstruzji,
- samo zero wiodące nie rozwiązuje problemu,
- skuteczne obejście: wewnętrzna konwersja `M83 -> Orca-like M82`,
- w tej konwersji trzeba zostawić `G92 E0` po przeliczonych retrakcjach,
- `G92 E0` z `layer change G-code` może zostać, ale nie wystarcza samo,
- finalny wrapper do użycia przez Orca to `g2z_wrapper_orca.py`,
- launchery systemowe nie wymagają zmian,
- wrapper ma raportować wartości i źródła patchowanych pól.



## A29. `ZORTRAX_INVENTURE_transfer_summary_2026-04-16.md`

# ZORTRAX INVENTURE — kompletne podsumowanie chata do przeniesienia

Data podsumowania: 2026-04-16  
Zakres: **Orca Slicer / G-code / `.zcode` dla Zortrax Inventure**, reverse engineering nagłówka, zastąpienie `g2z.jar` konwerterem Python, analiza bajtów nagłówka, testy `single/dual`, `native/external`, `fan speed`, `byte 72`, oraz poprawka kompatybilności dla **macOS**.

---

## 1. Główny stan projektu

Aktualny cel projektu jest dwojaki:

1. **Uzyskać działający workflow bez `g2z.jar`**, czyli:
   - `Orca -> G-code -> Python converter -> .zcode`
2. **Maksymalnie upodobnić wynik do plików z Z-Suite dla Inventure**:
   - przede wszystkim w nagłówku `.zcode`
   - a docelowo także w strumieniu komend

Na tym etapie:

- istnieje **działający pure Python konwerter** dla Inventure,
- potrafi wygenerować `.zcode` **bez używania `g2z.jar`**,
- poprawnie ustawia najważniejsze znane pola nagłówka,
- domyślnie ustawia **bajt `72` w stylu Z-Suite**:
  - `single -> 7`
  - `dual -> 5`

Ale nadal obowiązuje ważne zastrzeżenie:

- **strumień komend nie jest jeszcze binarnie 1:1 zgodny** z `g2z.jar + patcher` ani z Z-Suite we wszystkich przypadkach,
- nagłówek jest już opanowany dużo lepiej niż treść całego pliku.

---

## 2. Najważniejsze potwierdzone pola nagłówka classic `.zcode` dla Inventure

To pola, które należy traktować jako **potwierdzone roboczo**:

- `54..57` — czas druku
- `58..60` — triplet trybu zadania / kompatybilności
- `61` — printer id
- `62` — materiał modelowy
- `63` — warstwa
- `64` — jakość
- `65` — infill
- `66` — support angle / parametr supportu
- `68..71` — wersja software / Z-Suite
- `73..74` — długość filamentu modelowego
- `77..78` — długość filamentu supportowego
- `85` — materiał supportowy
- `127` — CRC nagłówka

Dodatkowo:

- `50..53` — **bardzo mocny kandydat na licznik komend**
- `72` — **mocna hipoteza: klasa/pochodzenie pliku lub tryb generatora**
- `67`, `75..76`, `79..84`, `86`, `87..126` — nadal nieustalone

---

## 3. Ustalenie o bajtach `58..60`

To jest już stabilna logika projektu:

### Potwierdzone reguły
- **single-material** -> `01 02 01`
- **dual + BASF Ultrafuse BVOH** -> `01 02 01`
- **dual + Z-SUPPORT** -> `01 03 00`
- **dual + Z-SUPPORT Plus** -> `01 03 00`
- **dual + Z-SUPPORT Premium** -> `01 03 00`

Wniosek:
- rodzina **Z-SUPPORT / Plus / Premium** wymaga `01 03 00`
- **single** oraz **BASF BVOH** używają `01 02 01`

To pole należy traktować jako jeden z najważniejszych elementów zgodności materiałowej dla Inventure.

---

## 4. Potwierdzone mapowanie materiałów

### 4.1. Natywne materiały Zortrax
- `Z-ULTRAT` -> `0x01`
- `Z-GLASS` -> `0x02`
- `Z-HIPS` -> `0x03`
- `Z-PCABS` -> `0x04`
- `Z-PETG` -> `0x05`
- `Z-ULTRAT PLUS` -> `0x06`
- `Z-SUPPORT` -> `0x07`
- `Z-ESD` -> `0x08`
- `Z-PHA` -> `0x09`
- `Z-PLA` -> `0x0A`
- `Z-PLA PRO` -> `0x0B`
- `Z-ASA PRO` -> `0x0C`
- `Z-SUPPORT PLUS` -> `0x0D`
- `Z-SEMIFLEX` -> `0x0E`
- `Z-FLEX` -> `0x0F`
- `Z-NYLON` -> `0x10`
- `Z-SUPPORT PREMIUM` -> `0x11`
- `Z-PEEK` -> `0x12`

### 4.2. Materiały external / open
- `ABS-BASED FILAMENT` -> `0x81`
- `GLASS-TYPE FILAMENT` -> `0x84`
- `FLEX-BASED FILAMENT` -> `0x85`
- `PLA-BASED FILAMENT` -> `0x86`
- `PETG-BASED FILAMENT` -> `0x87`
- `NYLON-BASED FILAMENT` -> `0x89`
- `ULTRAT-BASED FILAMENT` -> `0x91`
- `ESD PETG-BASED FILAMENT` -> `0x92`
- `PLA PRO-BASED FILAMENT` -> `0x94`
- `ASA PRO-BASED FILAMENT` -> `0x95`
- `SEMIFLEX-BASED FILAMENT` -> `0x96`

### 4.3. Support BASF
Najważniejsze aktywne ustalenie:
- `BASF ULTRAFUSE BVOH` -> **`0x17`**

Aliasy:
- `BVOH`
- `ULTRAFUSE BVOH`
- `BASF BVOH`

powinny też mapować do `0x17`.

---

## 5. CRC

CRC jest traktowane jako **potwierdzone**:

- algorytm CRC używany w patcherze/converterze jest poprawny,
- `127` to CRC nagłówka,
- jeśli drukarka zgłasza problem materiałowy, to pierwszych przyczyn należy szukać w:
  - `58..60`
  - `62`
  - `85`
  - relacji model/support
- a nie w samym CRC.

---

## 6. Kluczowe ustalenie o bajcie `72`

### 6.1. Co wynikało z plików Z-Suite
Dla referencyjnych plików Z-Suite dla Inventure wyszedł bardzo silny wzorzec:

- **Z-Suite single** -> `72 = 7`
- **Z-Suite dual** -> `72 = 5`

To było potwierdzone dla:
- native single
- native dual
- external single
- external dual

### 6.2. Co robi `g2z.jar`
Zostało sprawdzone bezpośrednio:
- **`g2z.jar` sam wpisuje `72 = 6`**
- to nie był efekt patchera
- patcher początkowo w ogóle nie nadpisywał `72`

### 6.3. Wniosek
Najrozsądniejsza interpretacja na teraz:
- `72` **nie jest prostą flagą single/dual**
- jest raczej związane z:
  - pochodzeniem pliku
  - wariantem generatora
  - klasą workflow

Najlepszy model roboczy:
- **Z-Suite single** -> `7`
- **Z-Suite dual** -> `5`
- **g2z.jar workflow** -> `6`

### 6.4. Decyzja projektowa
Dla nowego Pythonowego konwertera przyjęto domyślnie:
- **`single -> 7`**
- **`dual -> 5`**

czyli:
- generator ma być **bardziej zbliżony do Z-Suite niż do `g2z.jar`**

Jednocześnie pozostawiono możliwość trybu zgodnego z JAR-em:
- `--byte72-mode jar` -> `72 = 6`
- `--byte72-mode zsuite` -> `single=7`, `dual=5`

Na końcu ustawiono domyślnie:
- **`zsuite`**

---

## 7. Aktualny pure Python konwerter

### Stan
Powstał plik:
- `g2z_wrapper_orca.py`

W aktualnej logice:
- działa **bez `g2z.jar`**
- generuje `.zcode` bez wywołania JAR-a
- domyślnie wpisuje `72` jak Z-Suite
- poprawnie ustawia:
  - `58..60`
  - `61`
  - `62`
  - `63`
  - `64`
  - `65`
  - `66`
  - `68..71`
  - `73..74`
  - `77..78`
  - `85`
  - `127`

### Uczciwe zastrzeżenie
Choć nagłówek jest już bardzo blisko referencji:
- **strumień komend nadal odbiega** od starego workflow `g2z.jar + patcher`
- rozmiar pliku i duża liczba bajtów w części roboczej nadal się różnią
- to oznacza, że:
  - nagłówek jest już dobrze odwzorowany,
  - ale pełny klon `g2z.jar` jeszcze nie jest ukończony.

---

## 8. Porównanie pure Python vs referencyjny `.zcode`

W jednym z ważnych testów:
- wejście: `20p_scale_erdinger_v1_0.2_Z-ULTRAT Plus_Z-HIPS_11h50m.gcode`
- referencja: `20p_scale_erdinger_v1_0.2_Z-ULTRAT Plus_Z-HIPS_11h50m.zcode`

Wynik:
- nagłówek zgadzał się w prawie wszystkich kluczowych polach:
  - `54..57`
  - `58..60`
  - `61`
  - `62`
  - `63`
  - `64`
  - `65`
  - `66`
  - `73..74`
  - `77..78`
  - `85`
- różniły się głównie:
  - `50..53`
  - `72`
  - `127` (CRC, naturalnie po zmianach)
- natomiast **cały strumień komend** nadal różnił się bardzo mocno

Wniosek:
- pure Python jest już dobry jako **generator z poprawnym nagłówkiem**
- ale nie jest jeszcze pełnym binarnym odpowiednikiem referencyjnego `.zcode`

---

## 9. Reverse engineering nieznanych pól nagłówka

### 9.1. Pola zielone — potwierdzone
- `54..57`
- `58..60`
- `61`
- `62`
- `63`
- `64`
- `65`
- `66`
- `68..71`
- `73..74`
- `77..78`
- `85`
- `127`

### 9.2. Pola żółte — mocne hipotezy
- `0..4` — sygnatura `ZCode`
- `16..39` — stałe pola formatu / techniczne parametry maszyny
- `50..53` — licznik komend
- `72` — klasa źródła pliku / tryb generatora

### 9.3. Pola czerwone — nadal nieustalone
- `5..15`
- `40..49`
- `67`
- `75..76`
- `79..84`
- `86`
- `87..126`

---

## 10. Wynik porównań native vs external

Bardzo ważne ustalenie:
- **external materials nie wprowadzają nowej klasy nieznanych bajtów**
- external pliki zachowują ten sam wzorzec co odpowiadające im klasy Z-Suite:
  - external single zachowuje wzorzec single (`72 = 7`)
  - external dual zachowuje wzorzec dual (`72 = 5`)

Zmieniają się głównie:
- `62` — model material
- `85` — support material
- `127` — CRC

Wniosek:
- **external nie tworzy nowego “trybu nagłówka”**
- wygląda jak zwykły Z-Suite single/dual z innym kodem materiału

---

## 11. Wynik porównań fan speed: `0%`, `100%`, `Auto`

Porównano trzy pliki:
- `Fan speed: 0%`
- `Fan speed: 100%`
- `Fan speed: Auto`

Wniosek:
- **fan speed nie ujawnił nowych nieznanych pól nagłówka**
- zmieniały się tylko:
  - `50..53`
  - `54..57`
  - `127`

Co z tego wynika:
- `50..53` jeszcze mocniej wygląda na **licznik komend**
- `54..57` to nadal **czas druku**
- `54` sam w sobie **nie jest flagą Auto**

Szczególnie ważne:
- `0%` i `100%` miały ten sam czas -> `54..57` bez zmian
- dopiero `Auto` zmieniło czas o 1 sekundę -> zmienił się najmłodszy bajt pola czasu

Wniosek:
- **bajt 54 nie jest od „Auto on/off”**
- jest po prostu najmłodszym bajtem pola `54..57 = print time`

---

## 12. Wynik porównań external single/dual

Dla:
- external single
- external dual

wyszło:
- brak nowych osobnych ukrytych bajtów dla external,
- `72` w Z-Suite zachowuje się tak samo jak dla native:
  - single -> `7`
  - dual -> `5`

To dodatkowo wzmocniło decyzję, żeby pure Python konwerter domyślnie ustawiał:
- `72 = 7` dla single
- `72 = 5` dla dual

---

## 13. Zasada klasyfikacji `single` vs `dual`

Aktywna logika:
- traktować jako **single**, jeśli:
  - support length = 0
  - albo support material jest faktycznie równy modelowi i nie ma realnego drugiego materiału
- w single:
  - `support_code = model_code`
  - `support_length_mm = 0`
  - `58..60 = 01 02 01`
  - `72 = 7` w trybie Z-Suite

Dla dual:
- `support_code` pozostaje realnym materiałem supportowym
- `support_length_mm` ma wartość > 0
- `58..60` zależy od klasy supportu:
  - Z-SUPPORT family -> `01 03 00`
  - BASF BVOH -> `01 02 01`
- `72 = 5` w trybie Z-Suite

---

## 14. Ustalenia o `g2z.jar`

### Co zostało potwierdzone
- `g2z.jar` wpisuje `72 = 6`
- nie daje nagłówka tak podobnego do Z-Suite jak chcemy dla finalnego workflow
- wygenerowane przez JAR pliki nadal wymagają patchowania nagłówka

### Wniosek projektowy
`g2z.jar` nie jest już punktem końcowym projektu, tylko:
- źródłem referencji,
- źródłem do reverse engineeringu,
- punktem porównawczym

Docelowy kierunek to:
- **pure Python bez `g2z.jar`**

---

## 15. Test innej drukarki — `.zcodex2`

Został wykonany test pliku z Z-Suite dla:
- **Zortrax M300 Dual**

Wniosek:
- to nie był classic `.zcode`, tylko **`.zcodex2`**
- ma całkowicie inny format:
  - długość bloku JSON na początku
  - JSON metadata
  - dalsze sekcje kontenera
- ten plik **nie nadaje się do wyciągania wniosków o offsetach 0..127 dla Inventure**

Decyzja:
- traktować to tylko jako test kontrolny
- nie używać do wnioskowania o bajtach Inventure

---

## 16. macOS — ostatni błąd i poprawka

### 16.1. Co się stało
Na macOS pojawił się błąd w logu:
- `TypeError: write_text() got an unexpected keyword argument 'newline'`

Log pokazał jednocześnie:
- Python: `/usr/bin/python3`
- Java: `/usr/local/opt/openjdk/bin/java`

Czyli:
- Java była już poprawnie wykrywana
- problem był w kompatybilności wrappera z systemowym Pythonem Apple

### 16.2. Diagnoza
Problem:
- `Path.write_text(..., newline="\n")` nie działa w tym interpreterze

### 16.3. Poprawka
Zmieniono zapis na wersję kompatybilną:
```python
with open(work_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(normalized)
```

### 16.4. Wniosek
Ta poprawka:
- jest kompatybilna z macOS,
- powinna być kompatybilna z Windowsem,
- nie pogarsza Windowsowego działania,
- eliminuje konkretny błąd Apple Python.

---

## 17. Windows vs macOS — kompatybilność wrappera

Aktualna poprawka zapisu pliku:
- jest bardziej uniwersalna niż poprzednia wersja `Path.write_text(newline=...)`
- powinna działać:
  - na Windows
  - na macOS
  - na standardowym Pythonie 3

Jednocześnie nie przeprowadzono w tej rozmowie pełnego end-to-end testu na realnym środowisku Windows po tej ostatniej poprawce, więc:
- logicznie i technicznie powinna być zgodna,
- ale pełna weryfikacja praktyczna nadal wymaga realnego uruchomienia.

---

## 18. Najważniejsze aktualne pliki robocze

Najważniejszy plik roboczy projektu na tym etapie:
- `g2z_wrapper_orca.py`

To jest obecnie:
- główny konwerter / wrapper
- pure Python
- bez `g2z.jar`
- z domyślnym `byte72-mode = zsuite`

Ważne pliki testowe / referencyjne używane w tej fazie:
- różne pary `gcode <-> zcode` dla:
  - single
  - dual
  - native
  - external
  - BASF BVOH
  - Z-SUPPORT Premium
  - fan speed 0 / 100 / auto
- dodatkowo log:
  - `orca_postprocess_last.log` do diagnozy błędu macOS

---

## 19. Aktualna rekomendacja operacyjna

### Dla dalszego rozwoju
Najważniejszy następny krok to:
- nie tyle dalsze zgadywanie kolejnych czerwonych pól,
- tylko **dopracowanie strumienia komend w pure Python konwerterze**

Nagłówek jest już stosunkowo dobrze odwzorowany.
Największy brak to nadal:
- zgodność treści `.zcode`, nie tylko samego headera

### Dla bieżącego użycia
Jeśli celem jest plik bardziej podobny do Z-Suite:
- używać domyślnego trybu `byte72 = zsuite`

Jeśli z jakiegoś powodu trzeba emulować zachowanie JAR:
- używać `--byte72-mode jar`

---

## 20. Najkrótsze streszczenie

Jeśli trzeba przenieść tylko minimum:

- powstał **pure Python konwerter** `g2z_wrapper_orca.py`
- działa **bez `g2z.jar`**
- domyślnie ustawia:
  - `72 = 7` dla single
  - `72 = 5` dla dual
- potwierdzone pola nagłówka:
  - `54..57`, `58..60`, `61`, `62`, `63`, `64`, `65`, `66`, `68..71`, `73..74`, `77..78`, `85`, `127`
- `50..53` to bardzo mocny kandydat na licznik komend
- external materials nie wprowadzają nowego ukrytego trybu nagłówka
- fan speed nie ujawnił nowych nieznanych pól; `54` nie jest flagą Auto
- `g2z.jar` wpisuje `72 = 6`
- pliki Z-Suite dla Inventure dają mocny wzorzec:
  - single -> `72 = 7`
  - dual -> `72 = 5`
- macOS błąd z `write_text(newline=...)` został poprawiony przez przejście na zwykłe `open(..., newline="\n")`
- nagłówek jest już opanowany dużo lepiej niż cały strumień komend
- następny główny cel: **zbliżyć treść `.zcode` do referencji, nie tylko header**

---

## 21. Starter prompt do nowego chatu

Można wkleić taki tekst:

> Pracujemy nad Zortrax Inventure.
>
> Zachowaj ten kontekst:
> - aktywny plik to `g2z_wrapper_orca.py`
> - to jest już pure Python konwerter bez `g2z.jar`
> - domyślnie ma działać w trybie Z-Suite dla bajtu `72`:
>   - single -> `7`
>   - dual -> `5`
> - `g2z.jar` wpisuje `72 = 6`, ale to nie jest już docelowe zachowanie
> - potwierdzone pola nagłówka `.zcode`: `54..57`, `58..60`, `61`, `62`, `63`, `64`, `65`, `66`, `68..71`, `73..74`, `77..78`, `85`, `127`
> - `50..53` to bardzo mocny kandydat na licznik komend
> - external materials nie wprowadzają nowego osobnego trybu nagłówka
> - fan speed `0/100/auto` nie ujawnił nowych ukrytych pól; `54` nie jest flagą Auto
> - macOS miał błąd `write_text(..., newline=...)`; poprawka to użycie zwykłego `open(..., newline="\n")`
> - największy otwarty temat to nie header, tylko dopracowanie strumienia komend tak, by pure Python był bliżej referencji z Z-Suite / starego workflow


## A30. `Zortrax_Inventure_transfer_v3.md`

# ZORTRAX INVENTURE – FINAL TRANSFER (v3)

## 1. Current State
- Active converter: pure Python (no g2z.jar)
- Version: 2026.04.25-zsuite-machine-v3
- Supports:
  - START_MACHINE
  - SPECIAL_CLEAN
  - END_MACHINE

## 2. Special Markers

### Start
;ZORTRAX_START_MACHINE AUTO/SINGLE/DUAL

### Clean
;ZORTRAX_SPECIAL_CLEAN AUTO/SINGLE/DUAL/T0/T1

### End
;ZORTRAX_END_MACHINE AUTO/SINGLE/DUAL

## 3. Key Finding – Cleaning

Cleaning is implemented using:
03 11 XX

Mapping:
- 00 GarbageCenter
- 05 ModelBrushAvoid
- 06 SupportBrushAvoid
- 09 ModelGarbageOutside
- 0A SupportGarbageOutside

## 4. Critical Fix v3

Problem:
- slow movement after cleaning

Solution:
Restore feedrate after last cleaning position

Single:
F4800

Dual:
F3600

## 5. Behavior Logic

AUTO:
- detects single/dual + active tool

DUAL:
- full sequence both heads

T0/T1:
- single head only

## 6. Orca Integration

Printer Settings → Machine G-code:

Start:
;ZORTRAX_START_MACHINE AUTO

Tool change:
;ZORTRAX_SPECIAL_CLEAN AUTO

End:
;ZORTRAX_END_MACHINE AUTO

## 7. Comparison vs g2z.jar

g2z.jar:
- ignores markers
- does NOT generate full Z-Suite sequences

Python v3:
- generates full start/clean/end sequences

## 8. Status

Header: OK
Cleaning: MATCH
Start/End: MATCH
Motion restore: FIXED

## 9. Next Step

Remaining:
- full command stream parity with Z-Suite


## A31. `Zortrax_Inventure_v146_temperature_speed_audit.md`

# Audyt v1.4.6 — temperatury filamentów i prędkości processów
Ten raport dotyczy paczki `v1.4.6_chamber_as_bed` wygenerowanej z ostatnich presetów single/dual użytkownika.
## Wniosek główny
- Temperatury w presetach **nie są w całości bezpośrednim odczytem z próbek Z-Suite**. Są mieszanką: istniejących wartości z presetów Orca, wcześniejszej bazy materiałowej projektu oraz transformacji `chamber = bed`.
- Analiza programu Z-Suite dała nazwy pól i logikę rozdzielenia purge/retract/brushing/tower, ale **nie dała kompletnej tabeli temperatur i speedów procesu**.
- Prędkości w sekcji `process/*` w v1.4.6 **nie były przebudowywane z Z-Suite**. Zostały zachowane z przesłanych presetów; zmieniono tylko post-process w części processów oraz ustawienia single/dual support.
- `chamber = bed` oznacza, że wartości Orca plate-temp zostały zrównane z efektywną komorą, bo Inventure nie ma grzanego stołu. To jest mapowanie integracyjne dla Orca/konwertera, a nie dowód, że każdy profil ma natywną wartość Z-Suite.
## Filamenty — wartości po `chamber = bed`
| Filament | Type | Nozzle initial | Nozzle | Chamber | Hot/bed | Eng | Textured | Cool | Supertack |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BASF Ultrafuse BVOH | BVOH | 220 | 220 | 95 | 95 | 95 | 95 | 95 | 95 |
| External ASA Pro | ABS | 255 | 255 | 100 | 100 | 100 | 100 | 100 | 100 |
| External ESD | PETG | 245 | 245 | 80 | 80 | 80 | 80 | 80 | 80 |
| External FLEX | FLEX | 225 | 225 | 60 | 60 | 60 | 60 | 60 | 60 |
| External GLASS | PETG | 245 | 245 | 80 | 80 | 80 | 80 | 80 | 80 |
| External HIPS | ABS | 245 | 245 | 90 | 90 | 90 | 90 | 90 | 90 |
| External NYLON | ABS | 260 | 260 | 90 | 90 | 90 | 90 | 90 | 90 |
| External PCABS | ABS | 270 | 270 | 110 | 110 | 110 | 110 | 110 | 110 |
| External PEEK | PEEK | 380 | 380 | 140 | 140 | 140 | 140 | 140 | 140 |
| External PETG | PETG | 240 | 240 | 80 | 80 | 80 | 80 | 80 | 80 |
| External PHA | PLA | 205 | 205 | 55 | 55 | 55 | 55 | 55 | 55 |
| External PLA Pro | PLA | 215 | 215 | 60 | 60 | 60 | 60 | 60 | 60 |
| External PLA | PLA | 225 | 220 | 60 | 60 | 60 | 60 | 60 | 60 |
| External SEMIFLEX | FLEX | 230 | 230 | 60 | 60 | 60 | 60 | 60 | 60 |
| External SUPPORT Plus | PVA | 220 | 220 | 80 | 80 | 80 | 80 | 80 | 80 |
| External SUPPORT Premium | BVOH | 255 | 255 | 90 | 90 | 90 | 90 | 90 | 90 |
| External SUPPORT | PVA | 225 | 225 | 60 | 60 | 60 | 60 | 60 | 60 |
| External ULTRAT Plus | ABS | 235 | 235 | 100 | 100 | 100 | 100 | 100 | 100 |
| External ULTRAT | ABS | 260 | 260 | 100 | 100 | 100 | 100 | 100 | 100 |
| Z-ASA Pro | ABS | 255 | 255 | 100 | 100 | 100 | 100 | 100 | 100 |
| Z-ESD | PETG | 245 | 245 | 80 | 80 | 80 | 80 | 80 | 80 |
| Z-FLEX | FLEX | 225 | 225 | 60 | 60 | 60 | 60 | 60 | 60 |
| Z-GLASS | PETG | 245 | 245 | 80 | 80 | 80 | 80 | 80 | 80 |
| Z-HIPS | ABS | 235 | 235 | 90 | 90 | 90 | 90 | 90 | 90 |
| Z-NYLON | ABS | 260 | 260 | 90 | 90 | 90 | 90 | 90 | 90 |
| Z-PCABS | ABS | 270 | 270 | 110 | 110 | 110 | 110 | 110 | 110 |
| Z-PETG | PETG | 240 | 240 | 80 | 80 | 80 | 80 | 80 | 80 |
| Z-PHA | PLA | 205 | 205 | 55 | 55 | 55 | 55 | 55 | 55 |
| Z-PLA Pro | PLA | 215 | 215 | 60 | 60 | 60 | 60 | 60 | 60 |
| Z-PLA | PLA | 225 | 220 | 60 | 60 | 60 | 60 | 60 | 60 |
| Z-SEMIFLEX | FLEX | 235 | 235 | 65 | 65 | 65 | 65 | 65 | 65 |
| Z-SUPPORT Plus | PVA | 220 | 220 | 80 | 80 | 80 | 80 | 80 | 80 |
| Z-SUPPORT Premium | BVOH | 255 | 255 | 90 | 90 | 90 | 90 | 90 | 90 |
| Z-SUPPORT | PVA | 220 | 220 | 60 | 60 | 60 | 60 | 60 | 60 |
| Z-ULTRAT Plus | ABS | 255 | 235 | 100 | 100 | 100 | 100 | 100 | 100 |
| Z-ULTRAT | ABS | 260 | 260 | 100 | 100 | 100 | 100 | 100 | 100 |

## SINGLE — process speed/acceleration/jerk values
| Process | initial_layer_speed | initial_layer_infill_speed | outer_wall_speed | inner_wall_speed | top_surface_speed | internal_solid_infill_speed | sparse_infill_speed | gap_infill_speed | support_speed | support_interface_speed | bridge_speed | travel_speed | default_acceleration | outer_wall_acceleration | inner_wall_acceleration | top_surface_acceleration | sparse_infill_acceleration | travel_acceleration | default_jerk | outer_wall_jerk | inner_wall_jerk | top_surface_jerk | infill_jerk | travel_jerk | wipe_tower_max_purge_speed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle - single | 10 | 10 | 40 | 50 | 40 | 50 | 50 | 40 | 50 | 50 | 25 | 100 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |
| 0.15mm Quality @Zortrax Inventure 0.4 nozzle - single | 30 | 60 | 40 | 60 | 40 | 60 | 60 | 40 | 60 | 60 | 25 | 100 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |
| 0.20mm Standard @Zortrax Inventure 0.4 nozzle - single | 30 | 60 | 40 | 60 | 40 | 80 | 80 | 40 | 80 | 80 | 25 | 120 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |
| 0.30mm Draft @Zortrax Inventure 0.4 nozzle - single | 30 | 60 | 40 | 60 | 40 | 80 | 80 | 40 | 80 | 80 | 25 | 120 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |

## DUAL — process speed/acceleration/jerk values
| Process | initial_layer_speed | initial_layer_infill_speed | outer_wall_speed | inner_wall_speed | top_surface_speed | internal_solid_infill_speed | sparse_infill_speed | gap_infill_speed | support_speed | support_interface_speed | bridge_speed | travel_speed | default_acceleration | outer_wall_acceleration | inner_wall_acceleration | top_surface_acceleration | sparse_infill_acceleration | travel_acceleration | default_jerk | outer_wall_jerk | inner_wall_jerk | top_surface_jerk | infill_jerk | travel_jerk | wipe_tower_max_purge_speed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle - dual | 10 | 10 | 40 | 50 | 40 | 50 | 50 | 40 | 50 | 50 | 25 | 100 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |
| 0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual | 30 | 60 | 40 | 60 | 40 | 60 | 60 | 40 | 60 | 60 | 25 | 100 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |
| 0.20mm Standard @Zortrax Inventure 0.4 nozzle - dual | 30 | 60 | 40 | 60 | 40 | 80 | 80 | 40 | 80 | 80 | 25 | 120 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |
| 0.30mm Draft @Zortrax Inventure 0.4 nozzle - dual | 30 | 60 | 60 | 100 | 40 | 120 | 120 | 40 | 120 | 120 | 25 | 120 | 500 | 400 | 500 | 300 | 600 | 800 | 0 | 9 | 9 | 9 | 9 | 12 | 40 |

## Porównanie z presetami wejściowymi
### SINGLE
- Zmian w speed/accel/jerk: `0`.
- Pozostałe zmiany processów:
  - `process/0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle - single.json`: `post_process`
  - `process/0.15mm Quality @Zortrax Inventure 0.4 nozzle - single.json`: `post_process`
  - `process/0.20mm Standard @Zortrax Inventure 0.4 nozzle - single.json`: `post_process`
### DUAL
- Zmian w speed/accel/jerk: `0`.
- Pozostałe zmiany processów:
  - `process/0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle - dual.json`: `post_process`
  - `process/0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual.json`: `post_process`
  - `process/0.20mm Standard @Zortrax Inventure 0.4 nozzle - dual.json`: `post_process`

## Rekomendacja
Nie należy opisywać obecnych wartości speed jako „Z-Suite-derived”. Są praktycznym profilem Orca. Jeśli chcesz profile prędkości bliższe Z-Suite, trzeba zrobić osobny etap: dekodować natywne `.zcode` z Z-Suite, zebrać `OP02 feedrate` wg area/type/layer-height/material, potem dopiero przepisać `process/*` na tabelę wynikową.


## A32. `Zortrax_Inventure_v148_process_speed_targets.csv`

```csv
mode,layer,outer,inner,internal,sparse,top,support,support_interface,travel,bridge,initial,initial_infill,skirt,tower
single,0.08,12,17,41,28,28,40,35,120,50,10,28,20,33
single,0.15,20,25,40,25,33,40,35,120,50,10,25,20,33
single,0.20,20,25,40,40,40,40,35,120,50,10,40,20,33
single,0.30,20,25,40,40,40,40,35,120,50,10,40,20,33
dual,0.08,10,29,53,54,33,58,35,120,50,17,54,20,33
dual,0.15,20,58,107,108,67,58,35,120,50,17,58,20,33
dual,0.20,20,58,103,108,67,58,35,120,50,17,58,20,33
dual,0.30,19,25,40,40,40,58,40,120,50,17,40,20,33

```


## A33. `Zortrax_Inventure_v148_Z_filament_inventory_gaps.csv`

```csv
filament,code,class,present,type,nozzle,nozzle_initial,chamber_as_bed,density,flow_ratio,max_vol_speed,retract_length,retract_speed,gaps,notes
Z-ABS,0x00,"legacy/native observed, opcjonalny",NIE,,,,,,,,,,brak presetu w aktualnym configu,
Z-ULTRAT,0x01,native,TAK,ABS,260,260,100,1.04,0.926,12,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; some profile data inferred/observed.
Z-GLASS,0x02,native,TAK,PETG,245,245,80,1.27,0.97,9,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,"Native code known; some dual samples existed, but full speed/temp matrix incomplete."
Z-HIPS,0x03,native,TAK,ABS,235,235,90,1.04,0.95,10,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs complete native samples.
Z-PCABS,0x04,native,TAK,ABS,270,270,110,1.1,0.94,9,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs complete native samples.
Z-PETG,0x05,native,TAK,PETG,240,240,80,1.27,0.97,9,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; config temps are preset-derived. External PETG-based classic .zcode now confirmed separately as 0x83.
Z-ULTRAT Plus,0x06,native,TAK,ABS,235,255,100,1.04,0.926,12,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs complete native samples.
Z-SUPPORT,0x07,native support,TAK,PVA,220,220,60,1.04,0.95,12,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brakuje rozdziału temp/profilu: support-role vs standalone/model-role; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs more real support-role samples for temp/retract/purge matrix.
Z-ESD,0x08,native,TAK,PETG,245,245,80,1.2,0.97,8,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs complete native samples.
Z-PHA,0x09,native,TAK,PLA,205,205,55,1.24,0.98,8,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs complete native samples.
Z-PLA,0x0A,native,TAK,PLA,220,225,60,1.24,0.98,12,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,"RFID/material code confirmed; many print samples, but full per-filament Z-Suite temp/speed matrix still incomplete."
Z-PLA Pro,0x0B,native,TAK,PLA,215,215,60,1.24,0.98,8,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs complete native samples.
Z-ASA Pro,0x0C,native,TAK,ABS,255,255,100,1.07,0.95,10,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; some profile data inferred/observed.
Z-SUPPORT Plus,0x0D,native support,TAK,PVA,220,220,80,1.04,0.95,4,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brakuje rozdziału temp/profilu: support-role vs standalone/model-role; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; needs more real support-role samples for temp/retract/purge matrix.
Z-SEMIFLEX,0x0E,native,TAK,FLEX,235,235,65,1.12,1,2,0.2,10,brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,RFID/native code confirmed; full native Z-Suite process sample still incomplete.
Z-FLEX,0x0F,native,TAK,FLEX,225,225,60,1.12,1,4,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; single start profile partially known.
Z-NYLON,0x10,native,TAK,ABS,260,260,90,1.14,0.95,8,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,Native code known; some profile data inferred/observed.
Z-SUPPORT Premium,0x11,native support,TAK,BVOH,255,255,90,1.04,0.95,8,nil,nil,brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brakuje rozdziału temp/profilu: support-role vs standalone/model-role; z b1/b3 support temp potwierdzony 220C przy PETG-based/chamber 60; preset ma 255C/90C; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode,"Native code 0x11 confirmed; b1/b3 as support with PETG-based confirmed support temp 220C and chamber 60C, while preset currently has standalone 255/90."
Z-PEEK,0x12,native,NIE,,,,,,,,,,brak presetu w aktualnym configu,

```


## A34. `Zortrax_Inventure_v148_Z_filament_inventory_gaps.md`

# Zortrax Inventure Orca v1.4.8 — inwentaryzacja filamentów Z-* i braki

Źródło: `Zortrax Inventure 0.4 nozzle - single_v1.4.8_ZSuite_OP02_speed_scaling.orca_printer` / dual ma identyczny zestaw filamentów.

W configu: 17 natywnych presetów Z-*. Brakuje: 2 z oczekiwanej listy z projektu.

## Dostępne presety Z-*

| Filament | Kod .zcode | Typ Orca | Nozzle | Initial | Chamber=bed | Główne braki |
|---|---:|---|---:|---:|---:|---|
| Z-ULTRAT | 0x01 | ABS | 260 | 260 | 100 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-GLASS | 0x02 | PETG | 245 | 245 | 80 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-HIPS | 0x03 | ABS | 235 | 235 | 90 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-PCABS | 0x04 | ABS | 270 | 270 | 110 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-PETG | 0x05 | PETG | 240 | 240 | 80 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-ULTRAT Plus | 0x06 | ABS | 235 | 255 | 100 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-SUPPORT | 0x07 | PVA | 220 | 220 | 60 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brakuje rozdziału temp/profilu: support-role vs standalone/model-role; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-ESD | 0x08 | PETG | 245 | 245 | 80 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-PHA | 0x09 | PLA | 205 | 205 | 55 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-PLA | 0x0A | PLA | 220 | 225 | 60 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-PLA Pro | 0x0B | PLA | 215 | 215 | 60 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-ASA Pro | 0x0C | ABS | 255 | 255 | 100 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-SUPPORT Plus | 0x0D | PVA | 220 | 220 | 80 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brakuje rozdziału temp/profilu: support-role vs standalone/model-role; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-SEMIFLEX | 0x0E | FLEX | 235 | 235 | 65 | brak pełnej natywnej próbki Z-Suite do walidacji temp/retract/speed; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-FLEX | 0x0F | FLEX | 225 | 225 | 60 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-NYLON | 0x10 | ABS | 260 | 260 | 90 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |
| Z-SUPPORT Premium | 0x11 | BVOH | 255 | 255 | 90 | brak materiałowej retrakcji w filament JSON; używa ustawień printer/process; brakuje rozdziału temp/profilu: support-role vs standalone/model-role; z b1/b3 support temp potwierdzony 220C przy PETG-based/chamber 60; preset ma 255C/90C; gęstość/flow/fan/max volumetric speed nie są w pełni zweryfikowane z natywnych .zcode |

## Brakujące presety natywne

| Filament | Kod | Status |
|---|---:|---|
| Z-ABS | 0x00 | brak presetu w aktualnym configu |
| Z-PEEK | 0x12 | brak presetu w aktualnym configu |

## Braki systemowe do uzupełnienia

- Materiałowe `filament_retraction_length` i `filament_retraction_speed` są w presetach `nil`; obecnie retrakcja pochodzi z printer/process. Po b1/b3 warto dodać przynajmniej potwierdzone wartości dla PETG-based/Z-SUPPORT Premium i potem dla natywnych Z-* w miarę próbek.
- Supporty `Z-SUPPORT`, `Z-SUPPORT Plus`, `Z-SUPPORT Premium` wymagają rozdzielenia profilu support-role od ewentualnego standalone/model-role. b1/b3 potwierdza dla Z-SUPPORT Premium jako support: 220°C przy komorze 60°C, podczas gdy preset ma 255°C/90°C.
- `Z-PEEK` nie ma natywnego presetu, jest tylko `External PEEK`.
- `Z-ABS` legacy/native observed 0x00 nie ma presetu. To może być opcjonalne, bo historycznie Z-ULTRAT bywał traktowany jako główny ABS-like materiał Inventure.
- Gęstość, flow ratio, fan/cooling i max volumetric speed są w większości wartościami presetowymi/inferowanymi; nie są jeszcze kompletne z natywnych `.zcode`.
- Temperatury chamber=bed są technicznie spójne dla Inventure, ale nie wszystkie są w 100% potwierdzone natywną próbką Z-Suite dla danego materiału.


## A35. `Zortrax_Inventure_v149_filament_profile_db.csv`

```csv
filament,zcode_code,external_canonical,support_role,single_nozzle,single_chamber_as_bed,single_retract_mm,single_retract_F,dual_nozzle,dual_chamber_as_bed,dual_retract_mm,dual_retract_F,fan_min,fan_max,flow_ratio,density,max_volumetric_speed,source,cooling_note
BASF Ultrafuse BVOH,0x17,,1,220,60,2.0,3600,220,40,2.0,3600,10,40,0.95,1.04,8,dual Inventure support role,Confirmed support role T1=220; triplet 01 02 01.
External ABS,0x81,ABS-BASED FILAMENT,0,275,80,0.8,2200,275,80,0.8,2200,0,30,0.95,1.04,8,"external profile mapped from Z-ABS; single Inventure + M200 Plus zcodex2, legacy/native code 0x00",ABS-like: low/auto fan; confirmed temps/retract from single and zcodex2.
External ASA Pro,0x95,ASA PRO-BASED FILAMENT,0,260,80,1.0,4400,260,80,1.0,4400,10,40,0.95,1.07,10,external profile mapped from Z-ASA Pro; single Inventure; dual pair sample still missing,ASA/ABS-like low cooling.
External ESD,0x92,ESD PETG-BASED FILAMENT,0,270,60,1.8,4800,270,60,2.0,4800,10,50,0.97,1.20,8,external profile mapped from Z-ESD; single and dual Inventure,ESD PETG-like.
External FLEX,0x87,FLEX-BASED FILAMENT,0,230,40,2.5,2100,230,40,2.5,2100,20,60,1.00,1.12,4,external profile mapped from Z-FLEX; single Inventure; dual pair sample missing,Flex sample confirmed in single.
External GLASS,0x84,GLASS-TYPE FILAMENT,0,225,60,2.0,4800,235,60,2.0,4800,15,55,0.97,1.27,9,external profile mapped from Z-GLASS; single and dual Inventure,PETG/glass-like auto cooling preserved.
External HIPS,0x81,ABS-BASED FILAMENT,0,235,90,1.0,2200,235,90,1.0,2200,10,60,0.95,1.04,10,external profile mapped from Z-HIPS; inferred/existing config; sample still missing,Not confirmed in newest Inventure samples; kept from existing config with ABS-like retract.
External NYLON,0x89,NYLON-BASED FILAMENT,0,250,80,2.0,4800,250,80,2.0,4800,10,35,0.95,1.14,8,external profile mapped from Z-NYLON; single Inventure; dual pair sample missing,Nylon low cooling.
External PCABS,0x81,ABS-BASED FILAMENT,0,290,85,1.2,4400,290,85,1.2,4400,10,40,0.94,1.10,8,external profile mapped from Z-PCABS; zcodex2 other printer,From Z-Suite zcodex2 M200 Plus; Inventure classic sample still missing.
External PEEK,0x12,PEEK-BASED FILAMENT,0,380,140,,,380,140,,,0,0,1.00,1.30,2,external profile mapped from Z-PEEK; rfid/header code known; sample missing,Native code known; thermal/retraction sample missing for Inventure.
External PETG,0x83,PETG-BASED FILAMENT,0,225,60,2.0,4800,235,60,2.0,4800,15,60,0.97,1.27,9,external profile mapped from Z-PETG; single and dual Inventure,PETG auto cooling preserved.
External PHA,0x86,PLA-BASED FILAMENT,0,205,55,1.0,2000,205,55,1.0,2000,35,100,0.98,1.24,8,external profile mapped from Z-PHA; inferred/existing config; sample still missing,No newest native sample; PLA/PHA-like cooling retained.
External PLA,0x86,PLA-BASED FILAMENT,0,210,30,1.0,2000,210,40,1.0,2000,30,100,0.98,1.24,12,external profile mapped from Z-PLA; single and dual Inventure,PLA; dual chamber higher than single in support jobs.
External PLA Pro,0x94,PLA PRO-BASED FILAMENT,0,207,30,1.5,2100,210,40,1.0,2000,25,100,0.98,1.24,8,external profile mapped from Z-PLA Pro; single and dual Inventure,PLA Pro; dual chamber higher than single in support jobs.
External SEMIFLEX,0x96,SEMIFLEX-BASED FILAMENT,0,225,50,2.0,2500,225,50,2.0,2500,20,60,1.00,1.12,4,external profile mapped from Z-SEMIFLEX; dual Inventure; single inferred from dual,Semi-flex dual sample confirmed; single classic sample still missing.
External SUPPORT,0x07,Z-SUPPORT,1,220,60,2.0,3600,220,40,2.0,3600,10,40,0.95,1.04,4,external profile mapped from Z-SUPPORT; inferred support-role; direct sample missing,"Support role; chamber is fallback, real dual chamber should come from model pair."
External SUPPORT Plus,0x0D,Z-SUPPORT PLUS,1,220,80,2.0,3600,220,40,2.0,3600,10,40,0.95,1.04,4,external profile mapped from Z-SUPPORT Plus; inferred support-role; direct sample missing,Support role; chamber fallback only.
External SUPPORT Premium,0x11,Z-SUPPORT PREMIUM,1,220,60,2.0,3600,220,40,2.0,3600,10,40,0.95,1.04,8,external profile mapped from Z-SUPPORT Premium; dual Inventure support role,"Confirmed support role T1=220; chamber comes from model/support job, not standalone support."
External ULTRAT,0x91,ULTRAT-BASED FILAMENT,0,260,80,1.0,4400,260,80,1.0,3000,10,80,0.926,1.04,12,external profile mapped from Z-ULTRAT; single Inventure; M300 Dual zcodex2 for ATP pair,"ULTRAT/ABS-like; dual retract from zcodex2 ATP sample, single from Inventure."
External ULTRAT Plus,0x91,ULTRAT-BASED FILAMENT,0,260,80,1.0,4400,260,80,1.0,2000,10,80,0.926,1.04,8,external profile mapped from Z-ULTRAT Plus; single and dual Inventure,High-temp ABS-like; dual retract differs from single in native samples.
Z-ABS,0x00,,0,275,80,0.8,2200,275,80,0.8,2200,0,30,0.95,1.04,8,"single Inventure + M200 Plus zcodex2, legacy/native code 0x00",ABS-like: low/auto fan; confirmed temps/retract from single and zcodex2.
Z-ASA Pro,0x0C,,0,260,80,1.0,4400,260,80,1.0,4400,10,40,0.95,1.07,10,single Inventure; dual pair sample still missing,ASA/ABS-like low cooling.
Z-ESD,0x08,,0,270,60,1.8,4800,270,60,2.0,4800,10,50,0.97,1.20,8,single and dual Inventure,ESD PETG-like.
Z-FLEX,0x0F,,0,230,40,2.5,2100,230,40,2.5,2100,20,60,1.00,1.12,4,single Inventure; dual pair sample missing,Flex sample confirmed in single.
Z-GLASS,0x02,,0,225,60,2.0,4800,235,60,2.0,4800,15,55,0.97,1.27,9,single and dual Inventure,PETG/glass-like auto cooling preserved.
Z-HIPS,0x03,,0,235,90,1.0,2200,235,90,1.0,2200,10,60,0.95,1.04,10,inferred/existing config; sample still missing,Not confirmed in newest Inventure samples; kept from existing config with ABS-like retract.
Z-NYLON,0x10,,0,250,80,2.0,4800,250,80,2.0,4800,10,35,0.95,1.14,8,single Inventure; dual pair sample missing,Nylon low cooling.
Z-PCABS,0x04,,0,290,85,1.2,4400,290,85,1.2,4400,10,40,0.94,1.10,8,zcodex2 other printer,From Z-Suite zcodex2 M200 Plus; Inventure classic sample still missing.
Z-PEEK,0x12,,0,380,140,,,380,140,,,0,0,1.00,1.30,2,rfid/header code known; sample missing,Native code known; thermal/retraction sample missing for Inventure.
Z-PETG,0x05,,0,225,60,2.0,4800,235,60,2.0,4800,15,60,0.97,1.27,9,single and dual Inventure,PETG auto cooling preserved.
Z-PHA,0x09,,0,205,55,1.0,2000,205,55,1.0,2000,35,100,0.98,1.24,8,inferred/existing config; sample still missing,No newest native sample; PLA/PHA-like cooling retained.
Z-PLA,0x0A,,0,210,30,1.0,2000,210,40,1.0,2000,30,100,0.98,1.24,12,single and dual Inventure,PLA; dual chamber higher than single in support jobs.
Z-PLA Pro,0x0B,,0,207,30,1.5,2100,210,40,1.0,2000,25,100,0.98,1.24,8,single and dual Inventure,PLA Pro; dual chamber higher than single in support jobs.
Z-SEMIFLEX,0x0E,,0,225,50,2.0,2500,225,50,2.0,2500,20,60,1.00,1.12,4,dual Inventure; single inferred from dual,Semi-flex dual sample confirmed; single classic sample still missing.
Z-SUPPORT,0x07,,1,220,60,2.0,3600,220,40,2.0,3600,10,40,0.95,1.04,4,inferred support-role; direct sample missing,"Support role; chamber is fallback, real dual chamber should come from model pair."
Z-SUPPORT ATP,0x13,,1,250,90,2.0,3600,250,90,2.0,3600,10,40,0.95,1.04,4,M300 Dual zcodex2 experimental; not confirmed Inventure classic,EXPERIMENTAL for Inventure; code observed in M300 Dual zcodex2 only.
Z-SUPPORT Plus,0x0D,,1,220,80,2.0,3600,220,40,2.0,3600,10,40,0.95,1.04,4,inferred support-role; direct sample missing,Support role; chamber fallback only.
Z-SUPPORT Premium,0x11,,1,220,60,2.0,3600,220,40,2.0,3600,10,40,0.95,1.04,8,dual Inventure support role,"Confirmed support role T1=220; chamber comes from model/support job, not standalone support."
Z-ULTRAT,0x01,,0,260,80,1.0,4400,260,80,1.0,3000,10,80,0.926,1.04,12,single Inventure; M300 Dual zcodex2 for ATP pair,"ULTRAT/ABS-like; dual retract from zcodex2 ATP sample, single from Inventure."
Z-ULTRAT Plus,0x06,,0,260,80,1.0,4400,260,80,1.0,2000,10,80,0.926,1.04,8,single and dual Inventure,High-temp ABS-like; dual retract differs from single in native samples.

```


## A36. `ZSUITE_dependencies_for_converter_report.md`

# Z-Suite.zip — analiza uruchomieniowa i zależności użyteczne dla konwertera

## 1. Czy Z-Suite da się uruchomić w tym środowisku?

Nie w pełnym trybie GUI. Paczka zawiera aplikację Windows x64:

- `Z-SUITE.exe` — PE32+ Windows GUI x86-64
- `Z-SUITE.dll` — .NET assembly, `netcoreapp3.1`
- `ZortraxNativeWrapper.dll` i `ZortraxNativeWrapperClassic.dll` — natywne DLL Windows x64

W środowisku testowym brakuje:

- `wine`
- `mono`
- `dotnet`

Dodatkowo aplikacja wymaga WindowsDesktop runtime, więc nawet zwykły .NET CLI nie wystarczyłby do pełnego GUI.

## 2. Minimalne środowisko do realnego uruchamiania Z-Suite jako oracle

Do prawdziwego uruchomienia Z-Suite potrzebne jest środowisko Windows x64 albo Wine z pełnym wsparciem GUI/CEF/WPF/WinForms. Z paczki wynika:

```json
{
  "tfm": "netcoreapp3.1",
  "framework": {
    "name": "Microsoft.WindowsDesktop.App",
    "version": "3.1.0"
  }
}
```

Wymagania praktyczne:

- Windows x64,
- .NET Core / Windows Desktop Runtime 3.1,
- biblioteki CEFSharp z paczki,
- natywne wrappery Zortrax,
- możliwość pracy z GUI.

Nie znaleziono prostego, jawnego CLI typu `Z-SUITE.exe --slice ...`, które można bezpiecznie wykorzystać w konwerterze.

## 3. Bezpośrednie zależności aplikacji Z-SUITE

Najważniejsze bezpośrednie zależności z `Z-SUITE.deps.json`:

- `CefSharp`
- `CefSharp.Core`
- `CefSharp.WinForms`
- `CefSharp.BrowserSubprocess.Core`
- `Microsoft.Extensions.Configuration.Json`
- `Microsoft.Extensions.DependencyInjection`
- `Microsoft.Windows.Compatibility`
- `NLog`
- `Newtonsoft.Json`
- `System.Reactive.Reference`
- `WpfAnimatedGif`

Dla naszego konwertera pure Python nie są to zależności runtime. Są przydatne tylko wtedy, gdy chcemy uruchamiać Z-Suite jako zewnętrzne narzędzie referencyjne.

## 4. Native wrappery

### `ZortraxNativeWrapper.dll`

Eksportuje głównie funkcje geometrii/slicingu/profili, m.in.:

- `PFSlicerGetSlices`
- `PFSolidCreateSlicer`
- `PFSolidCreateSlices`
- `PFSolidCreateSupportVolume`
- `PFProfileAddLine`
- `PFProfileAddArc`
- `PFProfileOffset`
- `PFProfileUnion`
- `PFProfileSubtract`
- `PFProfileFixSelfIntersections`

### `ZortraxNativeWrapperClassic.dll`

Eksportuje funkcje profili/sliced geometry dla klasycznego trybu, m.in.:

- `PFSolidCreateSlices`
- `PFCurveCreateFromProfile`
- `PFProfileAddLine`
- `PFProfileAddArc`
- `PFProfileOffset`
- `PFProfileUnion`
- `PFProfileSubtract`

Nie znaleziono eksportów typu `EncodeZCode`, `WriteZCode`, `ClassicZCodeCommandTable`. To sugeruje, że generowanie `.zcode` jest prowadzone w logice .NET albo przez nieeksportowane funkcje, a nie przez prosty publiczny interfejs DLL.

## 5. Najważniejsze nazwy wewnętrzne Z-Suite dla klasycznego Inventure

Z `Z-SUITE.dll` da się wyciągnąć cenne nazwy pól. Są one zgodne z logiką, którą mamy już w konwerterze:

### Toolchange / purge / retract

- `ES_RetractionBeforeChangeToModel`
- `ES_RetractionBeforeChangeToModelSpeed`
- `ES_RetractionBeforeChangeToSupport`
- `ES_RetractionBeforeChangeToSupportSpeed`
- `ES_PurgeAfterChangeToModel`
- `ES_PurgeAfterChangeToModelSpeed`
- `ES_PurgeAfterChangeToSupport`
- `ES_PurgeAfterChangeToSupportSpeed`
- `ES_ExtruderSwitchInFirmware`
- `ES_SwitchExtruder`

Wniosek dla konwertera:

- utrzymać osobne profile dla przejścia na model i na support,
- nie mieszać T0-clean single z T1→T0 dual toolchange,
- utrzymać rozdzielenie długości purge i prędkości purge,
- `E_SPEED_SCALE` powinien skalować feedrate, nie długości E.

### Brushing / cleaning

- `ES_SleepTimeBeforeBrushing`
- `ES_SleepTimeBeforeBrusning` — literówka istnieje w Z-Suite
- `ES_BrushingTimes`

Wniosek dla konwertera:

- `DWELL` przed brushingiem jest elementem zależnym od procedury, ale nie powinien być automatycznie dodawany do single T0 clean,
- single T0 clean v1.4.2, potwierdzony testem, pozostaje bez `DWELL 3000`.

### Waste/cooling tower

- `ES_WasteTowerEnable`
- `ES_WasteTowerSizeX`
- `ES_WasteTowerSizeY`
- `ES_WasteTowerCenterX`
- `ES_WasteTowerCenterY`
- `ES_WasteTowerOffset`
- `ES_WasteTowerSpeedModel`
- `ES_WasteTowerSpeedSupport`
- `ES_WasteTowerFeedModel`
- `ES_WasteTowerFeedSupport`
- `ES_CoolingTower`

Wniosek dla konwertera:

- drukowana wieża model/support na stole jest osobnym bytem od bin-clean/purge nad pojemnikiem,
- reguła LAB32 dotycząca splitu wipe/prime/cooling tower pozostaje właściwym kierunkiem,
- nie klasyfikować purge nad koszem jako drukowanej waste tower.

### Ekstrudery dla modelu/support/raft

- `ES_ExtruderNrModel`
- `ES_ExtruderNrSupport`
- `ES_ExtruderNrRaft`
- `ES_ExtruderNrRaftSurface`

Wniosek dla konwertera:

- warstwy raft/base-zone powinny mieć własną semantykę, niezależną od późniejszego supportu,
- aktualna logika LAB38/LAB26, w której raft-zone jest rozpoznawana po warstwach przed modelem, jest zgodna z modelem Z-Suite.

### Pozycje i przejścia model/support

- `ES_ToModelPositionX`
- `ES_ToModelPositionY`
- `ES_ToModelSlowMoveX`
- `ES_ToSupportPositionX`
- `ES_ToSupportPositionY`
- `ES_ToSupportSlowMoveX`
- `ES_GarbageAvoidingToModelPosX`
- `ES_GarbageAvoidingToModelPosY`
- `ES_GarbageAvoidingToSupportPosX`
- `ES_GarbageAvoidingToSupportPosY`

Wniosek dla konwertera:

- Z-Suite ma osobną logikę pozycji/obejścia dla przejścia do modelu i supportu,
- nasze potwierdzone ścieżki `SWITCH_T0`, `SWITCH_T1`, `POS00`, `T0 path`, `T1 path` powinny pozostać rozdzielone.

## 6. Klasy i elementy związane z Z-code

W `Z-SUITE.dll` widoczne są nazwy:

- `ZCodeStrategy`
- `ZCodeStrategyClassic`
- `ProjectFileService+<ZCodeStrategy>d__8`
- `ProjectFileService+<ZCodeStrategyClassic>d__9`
- `ZCodeMetadata`
- `CommandsTime`

Wniosek:

- Z-Suite ma osobną strategię dla classic Z-code,
- bez dekompilacji IL nie da się z samych stringów wydobyć pełnej tabeli opcode,
- ale nazwy potwierdzają, że istnieje oddzielna ścieżka classic, co pasuje do naszego podejścia.

## 7. Co można dodać do konwertera bez ryzyka

Bezpieczne dodatki:

1. Zachować słownik nazw Z-Suite `ES_*` jako dokumentację i diagnostykę.
2. Dodać audyt po konwersji:
   - single-material nie może mieć `area F4` w T0 clean,
   - single-material nie może mieć `DWELL 3000` w clean,
   - dual T1→T0 może mieć `F4 + FE + DWELL + T0 path + FD`.
3. Logować rozdział:
   - `purge_after_change_to_model`,
   - `purge_after_change_to_support`,
   - `retract_before_change_to_model`,
   - `retract_before_change_to_support`.
4. Utrzymać osobny profile store dla:
   - start single,
   - start dual,
   - layer clean single,
   - layer clean dual T0/T1,
   - toolchange clean T1→T0/T0→T1.
5. Utrzymać rozdział drukowanej tower geometry od purge/clean nad koszem.

## 8. Czego nie należy dodawać automatycznie tylko na podstawie tej analizy

Nie należy jeszcze zmieniać:

- opcode body,
- preview `0x12`,
- command count `50..53`,
- byte72,
- raft area mapping,
- sekwencji clean/purge,
- single T0 clean v1.4.2.

Powód: z paczki wyciągnięto nazwy i zależności, ale nie pełną dekompilację algorytmów ani wartości liczbowych wszystkich parametrów.

## 9. Praktyczny model dalszej pracy

Najlepsza ścieżka:

1. Konwerter pozostaje pure Python.
2. Z-Suite traktować jako oracle uruchamiany lokalnie na Windows u użytkownika.
3. Do automatycznych testów przygotować zestaw małych `.zcode`:
   - single T0 clean,
   - dual T0→T1,
   - dual T1→T0,
   - raft single,
   - raft dual,
   - pause.
4. Użytkownik otwiera je w Z-Suite / drukarce.
5. Wyniki wracają do konwertera jako potwierdzone reguły.

## 10. Podsumowanie dla implementacji

Najważniejsze zależności logiczne do utrzymania w konwerterze:

```text
single clean != dual toolchange clean
purge length != purge speed
retract before model != retract before support
purge after model != purge after support
brushing/dwell zależy od procedury, nie jest globalne
tower geometry != bin purge/clean
raft extruder/raft surface/support/model mają osobne semantyki
```

Aktualny `v1.4.2` single T0 clean jest zgodny z tym modelem i został praktycznie potwierdzony przez test.


## A37. `ZSUITE_OLD_STATIC_READOUT_REPORT.md`

# Z-Suite_old.zip — statyczny odczyt pod konwerter Inventure / Orca

## Zakres

Analizowany plik: `Z-Suite_old.zip`.

Paczka zawiera pełny rozpakowany folder aplikacji Windows, a nie sam instalator. Najważniejsze pliki:

- `Z-SUITE.dll` — główna monolityczna biblioteka .NET/WPF/CEF,
- `Z-SUITE.exe`,
- `ZortraxNativeWrapper.dll`,
- `ZortraxNativeWrapperClassic.dll`,
- `Profiles/default mode.zprof`,
- zasoby językowe `*/Z-SUITE.resources.dll`.

Runtime według `Z-SUITE.deps.json`: `.NETCoreApp v3.1`.

Daty plików wskazują wersję z okolic 2021-04-07. Jest to praktycznie starszy Windowsowy Z-Suite pośredni między bardzo starą linią classic a obecną 2.32.x.

## Najważniejszy wynik

Ta paczka daje trochę nowych nazw ustawień względem poprzedniego audytu, szczególnie z obszaru konturów, infillu, wejść/wyjść konturu oraz strategii uproszczenia konturów.

Nie daje natomiast gotowej tabeli liczbowej:

- opcode -> znaczenie,
- area byte -> nazwa,
- pełne profile materiałowe,
- algorytm preview / hotbed image,
- akceleracje per-feature.

## Co potwierdza dla obecnego konwertera

### 1. Z-Suite ma rozdzielone mechanizmy toolchange / purge / clean

W `Z-SUITE.dll` są obecne klucze:

```text
ES_RetractionBeforeChangeToModel
ES_RetractionBeforeChangeToModelSpeed
ES_RetractionBeforeChangeToSupport
ES_RetractionBeforeChangeToSupportSpeed
ES_PurgeAfterChangeToModel
ES_PurgeAfterChangeToModelSpeed
ES_PurgeAfterChangeToSupport
ES_PurgeAfterChangeToSupportSpeed
ES_SleepTimeBeforeBrushing
ES_BrushingTimes
ES_ExtruderSwitchInFirmware
ES_SwitchExtruder
```

To potwierdza, że obecne rozdzielenie w konwerterze:

- T0/model vs T1/support,
- purge po zmianie na model vs purge po zmianie na support,
- retrakcja przed zmianą na model vs support,
- clean/brushing jako osobny moduł,

jest zgodne z wewnętrzną semantyką Z-Suite.

### 2. Z-Suite rozróżnia raft, raft surface, model i support

Obecne są m.in.:

```text
ES_ExtruderNrModel
ES_ExtruderNrSupport
ES_ExtruderNrRaft
ES_ExtruderNrRaftSurface
ConfigDataTypeRaftBase
ConfigDataTypeRaftBase2
ConfigDataTypeRaftGrid
ConfigDataTypeRaftSurface
ConfigDataTypeSupportBase
ConfigDataTypeSupportBottom
ConfigDataTypeSupportGrid
ConfigDataTypeSupportInterface
ConfigDataTypeSupportSurface
```

To potwierdza regułę: raft/base-zone i raft interface nie mogą być traktowane jak zwykły support. Obecne reguły LAB26/LAB38 są zgodne z tym modelem.

### 3. Tower jest osobnym bytem, nie bin clean

Obecne są:

```text
ES_WasteTowerEnable
ES_WasteTowerSizeX
ES_WasteTowerSizeY
ES_WasteTowerCenterX
ES_WasteTowerCenterY
ES_WasteTowerOffset
ES_WasteTowerSpeedModel
ES_WasteTowerSpeedSupport
ES_WasteTowerFeedModel
ES_WasteTowerFeedSupport
```

To ponownie potwierdza rozdział:

```text
bin purge-clean nad pojemnikiem != drukowana tower na stole
```

### 4. Dodatkowe pola konturu/infill — nowe względem wcześniejszych audytów

Ta paczka ujawnia dodatkowe nazwy, które warto dodać do dokumentacji i audytu semantyki:

```text
ModelContour
ModelContourEntrance
ModelContourExit
ModelInvisibleContour
VisibleInfill
VisibleInfillContour
VisibleTopInfill
VisibleTopInfillContour
VisibleBottomInfill
VisibleBottomInfillContour
InvisibleInfill
InvisibleInfillContour
BridgeInfill
BridgeInfillContour
CutContour
CutContourStart
CutContourSecond
CutContourSecondStart
CutContourSupport
CutContourSupportStart
CutInfill
BottomInfill
TopInfill
OffsetsInnerContours
OffsetsOuterContours
PrintInternalContoursFirst
PolygonMinTimeContourSlow
SimplifyDistanceContour
ContourEntranceFeed
ContourExitFeed
ContourEntranceLength
ContourExitLength
ContourEntranceAngle
ContourExitAngle
```

Praktyczne znaczenie dla konwertera:

- warto zachować osobną semantykę dla wejścia/wyjścia konturu i seam,
- warto nie zlewać `VisibleInfill`, `InvisibleInfill`, `Top/BottomInfill` w jedną klasę bez potrzeby,
- `BridgeInfill` może wymagać osobnej klasyfikacji, jeśli pojawi się w natywnych `.zcode`,
- `CutContour/CutInfill` mogą odpowiadać specjalnym fragmentom ścieżek, ale bez próbek `.zcode` nie należy mapować ich na nowe area automatycznie.

### 5. Fan / cooling są dalej złożone

Obecne są m.in.:

```text
AutomaticFanSpeedEnabled
BR_FanSpeed
RAFT_FAN_ENABLE_AREA
RAFT_FAN_SPEED
Fan1
Fan2
```

To potwierdza, że `Fan Auto` w Z-Suite jest osobnym algorytmem. Aktualny konwerter powinien dalej bezpiecznie kodować realny `M106 S...` z Orca i clampować do `0..255`, ale nie ma podstaw do odtworzenia pełnej krzywej Z-Suite bez macierzy próbek.

## Native wrappery

`ZortraxNativeWrapperClassic.dll` eksportuje głównie funkcje geometrii/solid/mesh:

```text
CreateAnalysisHelper
DeleteAnalysisHelper
EnvironmentCreate
EnvironmentDestroy
Initialise
QueryArrays
QueryCounts
QueryDestroy
SolidAnalysisMesh
SolidClashes
SolidClose
SolidCompare
SolidConcatenate
SolidCopy
SolidCreateFromMesh
SolidDestroy
SolidFixOrientation
SolidFixSelfIntersections
SolidGetSelfIntersections
SolidIntersect
SolidIsBadOrientation
SolidIsClosed
SolidIsSelfIntersects
SolidOffset
SolidQuery
SolidReconstruct
SolidSimplify
SolidSplit
SolidSubtract
SolidThicknessMesh
SolidUnion
Terminate
ThreadRegister
ThreadUnregister
```

Nie są to bezpośrednie eksporty typu `WriteZCodeCommand` ani `EncodeOpcode`. Czyli z tego DLL nie da się prosto wyciągnąć tabeli opcode przez same eksporty.

## `default mode.zprof`

Plik `Profiles/default mode.zprof` jest gzipem z binarnym `.NET BinaryFormatter`.

Po rozpakowaniu widać m.in.:

```text
System.Collections.Generic.Dictionary`2[[System.String,...],[System.Byte[],...]]
Defaults
ProjectVersion
Zortrax.Printers, Version=2.7.0.0
Zortrax.Printers.JsonSerializationClasses.DefaultProfileToJson
<NozzleDiameter>k__BackingField
<LayerThickness>k__BackingField
<Quality>k__BackingField
<InfillName>k__BackingField
<InfillId>k__BackingField
<InfillDensity>k__BackingField
High
Medium
2.7.0.0
```

To potwierdza, że profil domyślny zawiera podstawowe wartości jakości/layer/infill, ale w tej postaci nie daje pełnej tabeli materiałów ani prędkości. Pełne odczytanie wymagałoby parsera BinaryFormatter albo uruchomienia kodu .NET z typami `Zortrax.Printers`.

## Co można bezpiecznie dodać do konwertera / dokumentacji

Nie zmieniać mechaniki ruchów tylko na podstawie stringów, ale dodać do audytu/dokumentacji:

```text
ZSUITE_OLD_2021_CONFIRMED_SEMANTICS = True
ZSUITE_CONTOUR_INFILL_FIELDS_CONFIRMED = True
ZSUITE_BRIDGE_INFILL_FIELD_PRESENT = True
ZSUITE_CUT_CONTOUR_FIELDS_PRESENT = True
```

Praktyczne wskazówki:

1. Nie scalać wszystkiego do `MODEL` / `SUPPORT`; Z-Suite ma bogatszą semantykę konturów, visible/invisible infill, top/bottom infill, bridge i cut paths.
2. Zachować `SEAM 0xDF` i `ZORTRAX_LAYER_META`, bo Z-Suite ma osobne wejścia/wyjścia konturu.
3. W OP02/speed process warto w przyszłości rozważyć oddzielne klasy: bridge infill, visible top/bottom infill i contour entrance/exit, jeśli pojawią się rozpoznawalne area w natywnych `.zcode`.
4. Fan Auto nadal wymaga testów próbkowych.
5. Akceleracje per-feature nadal nie są bezpośrednio dostępne.

## Co nadal wymaga próbek Z-Suite

- liczbowy mapping area -> semantyka dla nowych nazw typu Bridge/Cut/Visible/Invisible,
- czy i jak Inventure classic `.zcode` oznacza `BridgeInfill`,
- czy `ContourEntrance/Exit` ma własny area czy tylko krótkie ruchy z tym samym area,
- pełna reguła Fan Auto,
- pełne profile materiałów/prędkości dla brakujących filamentów.
