# Classic `.zcode` header and materials

## Confirmed header fields

| Offset | Meaning |
|---:|---|
| `54..57` | print time |
| `58..60` | job mode / compatibility triplet |
| `61` | printer id |
| `62` | model material |
| `63` | layer height encoded in hundredths of mm |
| `64` | quality |
| `65` | infill |
| `66` | support angle / support parameter |
| `68..71` | software / Z-Suite version |
| `73..74` | model filament length |
| `77..78` | support filament length |
| `85` | support material |
| `127` | header CRC |

## Triplet `58..60`

| Case | Value |
|---|---|
| single-material | `01 02 01` |
| dual + BASF Ultrafuse BVOH | `01 02 01` |
| dual + Z-SUPPORT | `01 03 00` |
| dual + Z-SUPPORT Plus | `01 03 00` |
| dual + Z-SUPPORT Premium | `01 03 00` |

## Native Zortrax materials

| Material | Code |
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

## External / open materials

| Material | Code |
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

| Material / alias | Code |
|---|---:|
| `BASF ULTRAFUSE BVOH` | `0x17` |
| `BVOH` | `0x17` |
| `ULTRAFUSE BVOH` | `0x17` |
| `BASF BVOH` | `0x17` |

## CRC

The converter recalculates header CRC after setting all header fields. If the printer reports a material error, first check `62`, `85`, `58..60`, and the model/support material relationship.
