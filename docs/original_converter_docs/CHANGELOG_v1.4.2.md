# CHANGELOG v1.4.2 LAB38-safe hotfix

- Naprawiono regresję self-check LAB38 po latest material DB refresh.
- Przywrócono ochronę single LAB38: single-material T0 clean nie używa dualowego T0 clean profile `F4 + DWELL`.
- Z-PLA single feed dla ścieżki LAB38-safe pozostaje `4800 / 2100 / 2100` i nie emituje zdublowanego feedrate przed trzecim ruchem E, jeśli F jest takie samo.
- Dual T1->T0 clean fix z v1.4.1 pozostaje bez zmian.
- Latest material DB 2026-05-03 pozostaje dołączona; hotfix dotyczy wyłącznie izolacji logiki single od dualowego T0 clean.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
