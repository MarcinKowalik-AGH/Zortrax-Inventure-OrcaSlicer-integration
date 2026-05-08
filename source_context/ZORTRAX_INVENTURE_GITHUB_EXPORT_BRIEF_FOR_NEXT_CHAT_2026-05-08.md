# Zortrax Inventure + OrcaSlicer — brief do przygotowania aktualizacji GitHub

**Data briefu:** 2026-05-08  
**Cel:** przekazać do nowego chatu komplet instrukcji potrzebnych do przygotowania kolejnej wersji projektu GitHub na bazie aktualnego stanu konwertera, presetów i ustaleń reverse engineeringu.

Repozytorium, które ma zostać zaktualizowane:

```text
https://github.com/MarcinKowalik-AGH/Zortrax-Inventure-OrcaSlicer-integration
```

---

## 1. Najkrótszy prompt dla nowego chatu

Wklej w nowym chacie:

```text
Przygotuj aktualizację projektu GitHub dla Zortrax Inventure + OrcaSlicer na podstawie aktualnych plików projektu. Główne źródło kontekstu to ZORTRAX_INVENTURE_PROJECT_SOURCE_MASTER_2026-05-05.md oraz najnowsza paczka Zortrax_Inventure_Orca_LATEST_v1.4.15_converter_v1.4.14_configs_2026-05-06.zip.

Celem jest przygotowanie kolejnej wersji repozytorium GitHub po polsku i angielsku: README, README_PL, CHANGELOG, RELEASE_NOTES, instrukcja instalacji Windows/macOS, opis plików, struktura folderów, ostrzeżenia testowe i checklisty. Zachowaj aktualną logikę projektu: konwerter pure Python do classic .zcode, v1.4.15 jako aktualna linia produkcyjna, v1.2.20 jako linia patchowa, presety v1.4.14_current_converter, oraz wszystkie ustalenia dotyczące ZORTRAX_* markerów, materiałów, chamber=bed, OP02, smart DUAL layer clean i polityki AUTO.
```

---

## 2. Aktualna wersja projektu

Aktualny stan roboczy projektu:

```text
Konwerter produkcyjny: v1.4.15_layer_clean_dual_smart_restore
Linia patchowa:        v1.2.20_layer_clean_dual_smart_restore
Presety Orca:          v1.4.14_current_converter
Główny transfer:       ZORTRAX_INVENTURE_PROJECT_SOURCE_MASTER_2026-05-05.md
Paczka latest:         Zortrax_Inventure_Orca_LATEST_v1.4.15_converter_v1.4.14_configs_2026-05-06.zip
```

Najważniejsza zasada instalacji konwertera:

```text
Zawsze podmieniać oba pliki:
- g2z_wrapper_orca.py
- g2z_wrapper_orca_base_lab14_known_good.py

Sama podmiana wrappera nie wystarcza.
```

---

## 3. Co musi wejść do nowej wersji GitHub

Z repozytorium należy zrobić nową wersję zawierającą:

```text
converter/
  g2z_wrapper_orca.py
  g2z_wrapper_orca_base_lab14_known_good.py
  run_g2z_orca_postprocess.bat
  run_g2z_orca_postprocess.sh
  run_g2z_orca_postprocess.command

orca_presets/
  Zortrax Inventure 0.4 nozzle - single_v1.4.14_current_converter.orca_printer
  Zortrax Inventure 0.4 nozzle - dual_v1.4.14_current_converter.orca_printer

rfid_optional/
  opcjonalne pliki .mfd, jeśli repo ma dalej przechowywać RFID

docs/
  README_PL.md
  README.md
  INSTALL_PL.md
  INSTALL.md
  CHANGELOG.md
  RELEASE_NOTES_PL.md
  RELEASE_NOTES.md
  MACHINE_GCODE_PL.md
  MACHINE_GCODE.md
  MATERIAL_DATABASE_PL.md
  MATERIAL_DATABASE.md
  TROUBLESHOOTING_PL.md
  TROUBLESHOOTING.md
  REVERSE_ENGINEERING_NOTES_PL.md
  REVERSE_ENGINEERING_NOTES.md
  PROFILE_SUFFIX_POLICY_PL.md
  PROFILE_SUFFIX_POLICY.md
  ZSUITE_AUTOMATRIX_PL.md
  ZSUITE_AUTOMATRIX.md

examples/
  przykładowe G-code / marker snippets

source_context/
  ZORTRAX_INVENTURE_PROJECT_SOURCE_MASTER_2026-05-05.md
```

---

## 4. Opis projektu po polsku — do README_PL.md

### Nazwa

```text
Zortrax Inventure + OrcaSlicer integration
```

### Opis krótki

Projekt umożliwia przygotowywanie plików dla drukarki **Zortrax Inventure** bezpośrednio z **OrcaSlicer**, z użyciem własnego konwertera pure Python z G-code do klasycznego formatu `.zcode`. Celem jest jak najwierniejsze odwzorowanie zachowania Z-Suite: nagłówka `.zcode`, materiałów, trybów single/dual, supportu, procedur startowych, czyszczenia głowic, toolchange, raft/seam/tower oraz metadanych używanych przez firmware Inventure.

### Co zawiera projekt

```text
- pure-Python converter G-code -> classic .zcode,
- presety OrcaSlicer dla Zortrax Inventure single i dual,
- markery Machine G-code ZORTRAX_* dla startu, toolchange, layer clean i end,
- baza materiałów Zortrax / External / support,
- logika chamber=bed dla Inventure,
- obsługa relative E / M83 przez konwersję do Orca-like M82,
- obsługa seam przez ZORTRAX_LAYER_META i area 0xDF,
- obsługa raft/base-zone, tower i OP02 speed semantics,
- hotfixy fan clamp M106 S 0..255,
- smart restore w DUAL layer-clean, aby nie zostawiać aktywnego supportu po końcu wydruku.
```

### Status

```text
Aktualny konwerter produkcyjny: v1.4.15
Aktualne presety: v1.4.14_current_converter
Status: testowane na realnej Orca i fizycznych wydrukach, ale projekt nadal jest reverse engineeringiem i wymaga ostrożności.
```

---

## 5. English README summary

### Project name

```text
Zortrax Inventure + OrcaSlicer integration
```

### Short description

This project enables generating printable **classic `.zcode` files for Zortrax Inventure** directly from **OrcaSlicer** using a pure-Python G-code to ZCode converter. The converter reproduces key Z-Suite behavior: ZCode header fields, material IDs, single/dual mode, support material handling, start procedures, nozzle cleaning, toolchange purge, layer cleaning, raft/seam/tower semantics, and metadata required by the Inventure firmware.

### Included components

```text
- pure-Python G-code -> classic .zcode converter,
- OrcaSlicer printer/filament/process presets for Zortrax Inventure,
- ZORTRAX_* Machine G-code markers,
- Zortrax and external material database,
- chamber-as-bed policy for Inventure,
- M83 relative extrusion handling via Orca-like M82 conversion,
- seam tagging via ZORTRAX_LAYER_META and area 0xDF,
- raft/base-zone and tower semantics,
- OP02 feedrate-derived process speed logic,
- M106 fan clamp to 0..255,
- smart DUAL layer-clean restore to avoid ending with the support nozzle active.
```

---

## 6. Instalacja — Windows

### Katalog

Użytkownik powinien utworzyć lub użyć:

```text
C:\Users\<USER>\OrcaScripts\
```

Dla aktualnego użytkownika z projektu:

```text
C:\Users\Marcin Kowalik\OrcaScripts\
```

### Skopiować

Do `OrcaScripts` skopiować:

```text
g2z_wrapper_orca.py
g2z_wrapper_orca_base_lab14_known_good.py
run_g2z_orca_postprocess.bat
```

### OrcaSlicer Post-processing scripts

W OrcaSlicer → Printer settings → Others → Post-processing scripts:

```text
C:\Users\Marcin Kowalik\OrcaScripts\run_g2z_orca_postprocess.bat
```

Jeżeli inny użytkownik Windows, zmienić ścieżkę.

---

## 7. Installation — macOS

### Folder

```text
/Users/<username>/OrcaScripts/
```

Dla aktualnego użytkownika z projektu:

```text
/Users/mkowalik/OrcaScripts/
```

### Copy files

```text
g2z_wrapper_orca.py
g2z_wrapper_orca_base_lab14_known_good.py
run_g2z_orca_postprocess.sh
run_g2z_orca_postprocess.command
```

Nadać uprawnienia:

```bash
chmod +x /Users/mkowalik/OrcaScripts/run_g2z_orca_postprocess.sh
chmod +x /Users/mkowalik/OrcaScripts/run_g2z_orca_postprocess.command
```

### OrcaSlicer Post-processing scripts

```text
/Users/mkowalik/OrcaScripts/run_g2z_orca_postprocess.command
```

---

## 8. Aktualne Machine G-code — DUAL

### File header G-code

Należy zachować pełny blok `ORCA METADATA` i `ZORTRAX ZSUITE HINTS` zgodny z aktualnymi presetami. Kluczowe pola:

```gcode
; ===== ORCA METADATA BEGIN =====
; mode=DUAL
; process={print_preset}
; layer_height={layer_height}
; initial_layer_print_height={initial_layer_print_height}
; printer_preset={printer_preset}
; profile_suffix_policy=CANONICAL_PREFIX_PLUS_USER_SUFFIX_ALLOWED
; zortrax_temperature_policy=ORCA_OVERRIDES_ZSUITE_DEFAULTS
; zortrax_chamber_source=ORCA_BED_AS_CHAMBER
; zortrax_chamber_as_bed=1
; chamber_equals_bed=1
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
; raft_layers={raft_layers}
; raft_contact_distance={raft_contact_distance}
; raft_expansion={raft_expansion}
; raft_first_layer_density={raft_first_layer_density}
; raft_first_layer_expansion={raft_first_layer_expansion}
; brim_type={brim_type}
; brim_width={brim_width}
; ===== ORCA METADATA END =====

; ===== ZORTRAX ZSUITE HINTS BEGIN =====
; zsuite_profile_schema=2
; zsuite_generator=orca_pure_python
; zsuite_target_machine=Inventure
; zsuite_classic_zcode=1
; zsuite_temperature_policy=ORCA_OVERRIDES_ZSUITE_DEFAULTS
; zsuite_chamber_source=ORCA_BED_AS_CHAMBER
; zsuite_profile_suffix_policy=CANONICAL_PREFIX_PLUS_USER_SUFFIX_ALLOWED
; zsuite_retraction_before_change_to_model={retract_length_toolchange[1]}
; zsuite_retraction_before_change_to_model_speed={retraction_speed[1]}
; zsuite_retraction_before_change_to_support={retract_length_toolchange[0]}
; zsuite_retraction_before_change_to_support_speed={retraction_speed[0]}
; zsuite_purge_after_change_to_model=AUTO
; zsuite_purge_after_change_to_model_speed={deretraction_speed[0]}
; zsuite_purge_after_change_to_support=AUTO
; zsuite_purge_after_change_to_support_speed={deretraction_speed[1]}
; zsuite_sleep_time_before_brushing=3000
; zsuite_brushing_times=AUTO
; zsuite_extruder_switch_in_firmware=1
; zsuite_bin_clean_enabled=1
; zsuite_bin_clean_t0_path=0A,08,09,07,0A,08,00
; zsuite_bin_clean_t1_path=09,07,0A,08,09,07,00
; zsuite_waste_tower_enable=AUTO
; zsuite_waste_tower_source=ORCA_PRIME_TOWER
; zsuite_waste_tower_model_area=0x1D
; zsuite_waste_tower_support_area=0x1E
; zsuite_op02_support_speed_areas=0x04,0x05,0x18
; zsuite_op02_support_interface_areas=0x1B,0x21
; zsuite_op02_tower_areas=0x1D,0x1E
; zsuite_op02_travel_area=0xFC
; zsuite_raft_layers={raft_layers}
; zsuite_brim_type={brim_type}
; zsuite_brim_width={brim_width}
; ===== ZORTRAX ZSUITE HINTS END =====
```

### Machine start G-code

```gcode
;ZORTRAX_START_MACHINE DUAL CHAMBER=AUTO T0_TEMP=AUTO T1_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO
```

### Change filament / Tool change G-code

```gcode
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} direction_model_support={previous_extruder}->{next_extruder} zsuite_direction=AUTO layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400
```

### Layer change G-code

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN DUAL EVERY=20 START_LAYER=10 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
;ZORTRAX_LAYER_META layer_num={layer_num} layer_z={layer_z}
```

### Machine end G-code

```gcode
;ZORTRAX_END_MACHINE AUTO
```

---

## 9. Aktualne Machine G-code — SINGLE

### Machine start G-code

```gcode
;ZORTRAX_START_MACHINE SINGLE CHAMBER=AUTO T0_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO
```

### Tool change / Change filament G-code

Zostawić puste.

### Layer change G-code

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
;ZORTRAX_LAYER_META layer_num={layer_num} layer_z={layer_z}
```

### Machine end G-code

```gcode
;ZORTRAX_END_MACHINE AUTO
```

File header single ma analogiczny `ORCA METADATA` i `ZORTRAX ZSUITE HINTS`, ale bez T1/toolchange support fields.

---

## 10. Najważniejsze reguły techniczne

### Temperatury

```text
Explicit marker value > Orca metadata / G-code > Z-Suite DB > fallback
```

`CHAMBER=AUTO`, `T0_TEMP=AUTO`, `T1_TEMP=AUTO` mają pozwalać użytkownikowi zmienić temperaturę w Orca, np. +5°C, i konwerter ma to przejąć.

### Chamber

Zortrax Inventure nie ma grzanego stołu. W Orca `bed/plate temp` jest używane jako nośnik temperatury komory.

### Speed scale

`E_SPEED_SCALE` i `RETRACT_SPEED_SCALE` dotyczą tylko procedur technicznych konwertera:

```text
START_MACHINE
START_PURGE
TOOLCHANGE_CLEAN
LAYER_CLEAN
```

Nie zmieniają normalnych prędkości druku z Process. Skalują `F`, nie długości E.

### Process speed

Normalne prędkości idą z:

```text
Process -> G-code F -> OP02 in .zcode
```

### Relative E / M83

Konwerter wykrywa `M83` i robi kopię roboczą Orca-like `M82`, zachowując fizyczne dystanse E i dodając potrzebne `G92 E0`.

### Fan

`M106 S` musi być clampowane do zakresu `0..255`. W realnej Orca zdarzyło się `M106 S2383706846`.

---

## 11. Najważniejsze materiały i kody

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
Z-SUPPORT ATP       0x13 eksperymentalne
BASF Ultrafuse BVOH 0x17
PETG-based external 0x83
```

---

## 12. Najważniejsze procedury clean

### Single T0 clean

```text
FE -> FE -> T0 brush path -> FD -> RESTORE E0
```

Bez `area F4`, bez `DWELL`, bez `SELECT T0`, bez dualowego toolchange context.

### Dual T1→T0 clean

```text
E -20 area F3
RESTORE E0
SELECT T0
POS 00
F480 area F4 E21
F2000 area FE E22
DWELL 3000
T0 path 0A->08->09->07->0A->08->00
F2000 area FD E21
RESTORE E0
```

### DUAL layer clean smart restore

Od `v1.4.15`:

```text
- czyści aktualny tool,
- czyści drugi tylko jeśli będzie jeszcze użyty później,
- na końcu przywraca pierwotnie aktywny tool.
```

---

## 13. Release notes PL — wersja GitHub

### v1.4.15 / aktualizacja GitHub

Najważniejsze zmiany:

```text
- pełny konwerter pure Python bez Z-Suite/g2z.jar w normalnym runtime,
- aktualizacja baz materiałów i presetów Orca,
- obsługa ZORTRAX_FILAMENT_PROFILE w Advanced,
- polityka nazw z dopiskami użytkownika,
- polityka temperatur ORCA_OVERRIDES_ZSUITE_DEFAULTS,
- CHAMBER=AUTO / T0_TEMP=AUTO / T1_TEMP=AUTO,
- E_SPEED_SCALE=AUTO / RETRACT_SPEED_SCALE=AUTO,
- M106 fan clamp do 0..255,
- DUAL layer clean smart restore,
- poprawione single T0 clean bez procedury ładowania,
- potwierdzone dual T1→T0 clean zgodne z Z-Suite,
- OP02 speed semantics dla process,
- raft/brim status udokumentowany,
- Z-SUPPORT ATP dodany jako eksperymentalny.
```

---

## 14. Release notes EN

### v1.4.15 / GitHub update

Highlights:

```text
- pure-Python converter, no Z-Suite/g2z.jar required at runtime,
- updated Orca material and printer presets,
- ZORTRAX_FILAMENT_PROFILE comments in Filament Advanced,
- canonical profile suffix policy,
- ORCA_OVERRIDES_ZSUITE_DEFAULTS temperature policy,
- CHAMBER=AUTO / T0_TEMP=AUTO / T1_TEMP=AUTO,
- E_SPEED_SCALE=AUTO / RETRACT_SPEED_SCALE=AUTO,
- M106 fan clamp to 0..255,
- DUAL layer-clean smart restore,
- confirmed safe single T0 clean,
- confirmed dual T1→T0 clean matching Z-Suite behavior,
- OP02 feedrate/process-speed semantics,
- documented raft/brim state,
- experimental Z-SUPPORT ATP support entry.
```

---

## 15. Jak wgrać do GitHub — wariant web

1. Wejdź do repozytorium GitHub.
2. Zrób kopię / branch, np.:

```text
release/v1.4.15
```

3. Usuń lub przenieś stare pliki, które są zastępowane.
4. Wgraj nową strukturę folderów:

```text
converter/
orca_presets/
docs/
examples/
source_context/
```

5. Dodaj opis commita:

```text
Update Zortrax Inventure Orca integration to v1.4.15
```

6. Otwórz Pull Request lub zmerguj branch.
7. Utwórz release:

```text
v1.4.15
```

8. Do release assets dodaj ZIP:

```text
Zortrax_Inventure_Orca_LATEST_v1.4.15_converter_v1.4.14_configs_2026-05-06.zip
```

---

## 16. Jak wgrać do GitHub — wariant git CLI

```bash
git clone https://github.com/MarcinKowalik-AGH/Zortrax-Inventure-OrcaSlicer-integration.git
cd Zortrax-Inventure-OrcaSlicer-integration

git checkout -b release/v1.4.15

# skopiować nowe foldery i pliki
# converter/, orca_presets/, docs/, examples/, source_context/

git add .
git commit -m "Update Zortrax Inventure Orca integration to v1.4.15"
git push origin release/v1.4.15
```

Na GitHub utworzyć Pull Request i release.

---

## 17. Ostrzeżenia do README

```text
- Projekt jest wynikiem reverse engineeringu formatu classic .zcode.
- Używać ostrożnie i testować najpierw krótkie wydruki.
- Nie drukować plików testowych oznaczonych TEST ONLY.
- Przy aktualizacji konwertera zawsze podmienić oba pliki .py.
- Dla single sekcja Tool change / Change filament musi być pusta.
- W Filament Advanced nie dodawać realnych komend M104/M109/G1/T0/T1, tylko komentarz ZORTRAX_FILAMENT_PROFILE.
- Z-SUPPORT ATP 0x13 jest eksperymentalny dla Inventure.
```

---

## 18. Checklist dla nowego chatu przed wygenerowaniem GitHub package

Nowy chat powinien sprawdzić:

```text
[ ] Czy w paczce jest v1.4.15 converter.
[ ] Czy są oba pliki .py.
[ ] Czy są launchery Windows/macOS.
[ ] Czy są presety single/dual v1.4.14_current_converter albo nowsze.
[ ] Czy README PL/EN opisuje CHAMBER=AUTO i chamber=bed.
[ ] Czy README PL/EN opisuje E_SPEED_SCALE/AUTO i RETRACT_SPEED_SCALE/AUTO.
[ ] Czy README PL/EN opisuje smart DUAL layer clean restore.
[ ] Czy jest informacja o profile suffix policy.
[ ] Czy jest instrukcja instalacji Windows/macOS.
[ ] Czy jest changelog i release notes.
[ ] Czy testy/diagnostyka są oznaczone jako TEST ONLY.
[ ] Czy Z-SUPPORT ATP jest opisany jako eksperymentalny.
```

---

## 19. Czego nie robić w nowym chacie

```text
- Nie wracać do g2z.jar jako runtime.
- Nie usuwać smart restore w DUAL layer-clean.
- Nie mieszać single T0 clean z dualowym T1→T0 clean.
- Nie ustawiać twardo CHAMBER=45/T0_TEMP=215/T1_TEMP=225 w normalnych presetach.
- Nie dawać EVERY=AUTO i START_LAYER=AUTO w layer clean.
- Nie traktować TYPE:Skirt automatycznie jak brim 0x22.
- Nie zmieniać ruchów tylko na podstawie stringów z Z-Suite bez próbek .zcode.
```

