# Presety OrcaSlicer

W katalogu `presets/` są dwa niezależne bundle `.orca_printer`.

## Dual

Plik:

```text
Zortrax Inventure 0.4 nozzle - dual.orca_printer
```

Zawartość:

- printer: `Zortrax Inventure 0.4 nozzle - dual`,
- nozzle: `0.4`, `0.4`,
- obszar: `135 x 135`,
- wysokość: `130`,
- domyślny process: `0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual`,
- domyślne filamenty: `Z-PLA`, `Z-SUPPORT`,
- min layer: `0.08`,
- max layer: `0.3`,
- `single_extruder_multi_material = 0`.

Processy:

| Process | Layer | First layer | Support filament |
|---|---:|---:|---:|
| `0.08mm Ultra Quality ... - dual` | `0.08` | `0.2` | `2` |
| `0.15mm Quality ... - dual` | `0.15` | `0.2` | `2` |
| `0.20mm Standard ... - dual` | `0.2` | `0.2` | `2` |
| `0.30mm Draft ... - dual` | `0.3` | `0.2` | `2` |

## Single

Plik:

```text
Zortrax Inventure 0.4 nozzle - single.orca_printer
```

Zawartość:

- printer: `Zortrax Inventure 0.4 nozzle - single`,
- nozzle: `0.4`,
- obszar: `135 x 135`,
- wysokość: `130`,
- domyślny process: `0.15mm Quality @Zortrax Inventure 0.4 nozzle - single`,
- domyślny filament: `Z-PLA`,
- min layer: `0.08`,
- max layer: `0.3`,
- `single_extruder_multi_material = 0`.

Processy single zachowują parametry technologiczne z dual, ale mają:

```text
support_filament = 0
support_interface_filament = 0
```

czyli nie używają T1 jako filamentu supportu.

## Filamenty

Oba bundle zawierają tę samą rodzinę filamentów:

- natywne Zortrax: `Z-PLA`, `Z-SUPPORT`, `Z-ULTRAT`, `Z-HIPS`, itd.,
- external: `External PLA`, `External PETG`, `External PEEK`, itd.,
- `BASF Ultrafuse BVOH`.

## Reguły utrzymania bundli

Przy zmianie nazwy presetu trzeba jednocześnie zaktualizować:

- `name`,
- `printer_settings_id`, `print_settings_id` albo `filament_settings_id`,
- nazwę pliku JSON w archiwum,
- wpis w `bundle_structure.json`,
- `compatible_printers`, jeśli preset procesu jest przypisany do konkretnej drukarki.
