# Zortrax Inventure / Orca v1.4.1 — całościowe podsumowanie wrappera i skryptów

## 1. Status wersji

**v1.4.1-production-LAB38-LAB42B-zsuite-t0-clean** jest wersją złożoną z potwierdzonych artefaktów:

- single: potwierdzony LAB38, odtworzony 1:1 bajtowo,
- dual: potwierdzony LAB42B open-file,
- baza: v1.2.7-e-speed-scale + LAB14/LAB20/LAB26/LAB30/LAB31/LAB32/LAB36/LAB38/LAB42B.

Ta wersja powstała po odrzuceniu błędnych ścieżek LAB39/LAB40/LAB41/LAB43_DIRECT.

## 2. Wrapper

Główny plik:

```text
converter/g2z_wrapper_orca.py
```

Baza konwersji:

```text
converter/g2z_wrapper_orca_base_lab14_known_good.py
```

Wrapper uruchamia bazowy konwerter, a następnie wykonuje potwierdzony postprocess semantyki:

- raft/base-zone,
- seam 0xDF,
- exact pause OP0F,
- cleanup non-print support w raft-zone,
- tower split T0/T1,
- patch header count i CRC.

## 3. Skrypty Orca

Windows:

```text
run_g2z_orca_postprocess.bat
```

macOS/Linux:

```text
run_g2z_orca_postprocess.sh
run_g2z_orca_postprocess.command
```

Skrypty mają stabilne nazwy. Nie należy tworzyć nowych nazw typu `v2`, `final2`, `fixed`, bo Orca ma wskazywać stabilny launcher.

## 4. Potwierdzone LAB-y w v1.4.1

### LAB14

Semantyka ruchu przed obszarem: pure E, no-E XY, low-E connector/seam/jump, real print move.

### LAB20

Seam/connector działa bez haczyka. Zachować logikę seam.

### LAB26

Raft area carry: Orca potrafi opisywać raft jako Support / Support interface, co trzeba mapować na RAFT_BOTTOM / RAFT_INTERFACE.

### LAB30

Non-print support w raft-zone nie może zostać supportem wiszącym w powietrzu. Ma iść w JUMP/JUMP_PATH.

### LAB31

Seam 0xDF zachowany.

### LAB32

Wipe/prime tower split T0/T1: realne ekstruzyjne ruchy tower rozdzielać według aktywnego narzędzia.

### LAB36

`PAUSE_PRINT` musi być przenoszony dokładnie 1:1 jako OP0F.

### LAB38

Single support=true + raft/base-zone działa. Jeśli `raft_layers > 0` i warstwa jest przed pierwszą warstwą modelu, traktować ją jako raft/base-zone niezależnie od `support=true/false`.

### LAB42B

Dual open-file działa dzięki poprawnym wielu LAYER/opcode 0x10 i `byte72=0`. Nie wracać do fast/minimal generatora.

## 5. Nagłówek `.zcode`

Potwierdzone pola:

```text
50..53  command count
54..57  czas druku
58..60  triplet trybu zadania
61      printer id
62      materiał modelu
63      layer
64      quality
65      infill
66      support angle
68..71  software version
72      klasa profilu/generatora, w LAB-ach najczęściej 0
73..74  długość filamentu modelu
77..78  długość filamentu supportu
85      materiał supportu
127     CRC nagłówka
```

CRC liczone jest algorytmem CRC8 poly 0xD5.

## 6. Materiały

Najważniejsze kody:

```text
Z-PLA              0x0A
Z-SUPPORT          0x07
Z-SUPPORT PLUS     0x0D
Z-SUPPORT PREMIUM  0x11
BASF BVOH          0x17 w `.zcode`/nagłówku
```

Nie mieszać kodów RFID `.mfd` z kodami `.zcode`.

## 7. Błędy, do których nie wolno wracać

- LAB39 fast/minimal — odrzucony.
- LAB40 — pełny shell z błędną strukturą nadal dawał error.
- LAB41 — samo cofnięcie 58..60 nie wystarczyło.
- LAB43_DIRECT — oba testy single/dual dały open file error.
- Nie opisywać reguł tylko w README; reguły muszą realnie być w kodzie.
- Nie rekonstruować LAB38/LAB42B z pamięci, używać artefaktów z tej paczki.

## 8. Self-check

Single LAB38 można zweryfikować:

```bash
python3 tools/reproduce_lab38_single.py
```

Jeżeli wynik nie jest 1:1, nie wolno traktować modyfikacji jako zachowującej LAB38.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
