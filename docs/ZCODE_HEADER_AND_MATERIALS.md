# Nagłówek classic `.zcode` i materiały

## Potwierdzone pola nagłówka

| Offset | Znaczenie |
|---:|---|
| `54..57` | czas druku |
| `58..60` | triplet trybu zadania / kompatybilności |
| `61` | printer id |
| `62` | materiał modelowy |
| `63` | wysokość warstwy zakodowana w setnych mm |
| `64` | quality |
| `65` | infill |
| `66` | support angle / parametr supportu |
| `68..71` | wersja software / Z-Suite |
| `73..74` | długość filamentu modelowego |
| `77..78` | długość filamentu supportowego |
| `85` | materiał supportowy |
| `127` | CRC nagłówka |

## Triplet `58..60`

| Przypadek | Wartość |
|---|---|
| single-material | `01 02 01` |
| dual + BASF Ultrafuse BVOH | `01 02 01` |
| dual + Z-SUPPORT | `01 03 00` |
| dual + Z-SUPPORT Plus | `01 03 00` |
| dual + Z-SUPPORT Premium | `01 03 00` |

## Natywne materiały Zortrax

| Materiał | Kod |
|---|---:|
| `Z-ULTRAT` | `0x01` |
| `Z-GLASS` | `0x02` |
| `Z-HIPS` | `0x03` |
| `Z-PCABS` | `0x04` |
| `Z-PETG` | `0x05` |
| `Z-ULTRAT PLUS` | `0x06` |
| `Z-SUPPORT` | `0x07` |
| `Z-ESD` | `0x08` |
| `Z-PHA` | `0x09` |
| `Z-PLA` | `0x0A` |
| `Z-PLA PRO` | `0x0B` |
| `Z-ASA PRO` | `0x0C` |
| `Z-SUPPORT PLUS` | `0x0D` |
| `Z-SEMIFLEX` | `0x0E` |
| `Z-FLEX` | `0x0F` |
| `Z-NYLON` | `0x10` |
| `Z-SUPPORT PREMIUM` | `0x11` |
| `Z-PEEK` | `0x12` |

## Materiały external / open

| Materiał | Kod |
|---|---:|
| `ABS-BASED FILAMENT` | `0x81` |
| `GLASS-TYPE FILAMENT` | `0x84` |
| `FLEX-BASED FILAMENT` | `0x85` |
| `PLA-BASED FILAMENT` | `0x86` |
| `PETG-BASED FILAMENT` | `0x87` |
| `NYLON-BASED FILAMENT` | `0x89` |
| `ULTRAT-BASED FILAMENT` | `0x91` |
| `ESD PETG-BASED FILAMENT` | `0x92` |
| `PLA PRO-BASED FILAMENT` | `0x94` |
| `ASA PRO-BASED FILAMENT` | `0x95` |
| `SEMIFLEX-BASED FILAMENT` | `0x96` |

## BASF support

| Materiał / alias | Kod |
|---|---:|
| `BASF ULTRAFUSE BVOH` | `0x17` |
| `BVOH` | `0x17` |
| `ULTRAFUSE BVOH` | `0x17` |
| `BASF BVOH` | `0x17` |

## CRC

CRC nagłówka jest przeliczane przez konwerter po ustawieniu pól. Jeżeli drukarka zgłasza błąd materiału, pierwsze pola do sprawdzenia to zwykle `62`, `85` i `58..60`, a nie samo CRC.
