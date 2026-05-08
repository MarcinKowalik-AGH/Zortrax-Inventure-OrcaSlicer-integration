# Reverse engineering notes — PL

Projekt jest oparty na analizie plików Z-Suite, plików `.zcode`, presetów Orca i testów fizycznych na drukarce.

Najważniejsze ustalenia:

- Normalny runtime nie wymaga Z-Suite ani `g2z.jar`.
- Potwierdzone pola nagłówka obejmują m.in. materiał modelu, materiał supportu, triplet trybu, długości filamentów i CRC.
- `byte72` nie jest prostą flagą single/dual.
- `OP02` odpowiada feedrate; normalne prędkości druku pochodzą z Process → G-code `F` → OP02.
- Bin purge/clean nad pojemnikiem to nie to samo co drukowana prime/cool/waste tower na stole.
- Nie zmieniać ruchów tylko na podstawie stringów z Z-Suite bez próbek `.zcode` i testu.
