# LAB38-safe hotfix v1.4.2

Powód: w paczce v1.4.1 po odświeżeniu bazy materiałów single LAB38 przestał być bajtowo identyczny z potwierdzoną referencją.

Objaw przed poprawką:
- `python3 tools/reproduce_lab38_single.py` zwracał `byte-for-byte equal: False`.
- Liczba komend wzrosła z 68404 do 68565.
- W single pojawiły się dualowe ruchy T0 `area F4` oraz dodatkowe feedrate/dwell.

Poprawka:
- Dla `meta.single_material == True` i T0 clean używany jest osobny single-safe clean body.
- Dualowy T0 clean `F480 area F4 -> F2000 area FE -> DWELL -> clean -> F2000 area FD` pozostaje tylko dla dual.

Wynik po poprawce:
- `python3 tools/reproduce_lab38_single.py` zwraca `byte-for-byte equal: True`.
- SHA256 referencji i wygenerowanego pliku: `4b737be14d2d553a7ce9ebce5c2706d37dae1cd2a5021a99fe6c9e464e00dfed`.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
