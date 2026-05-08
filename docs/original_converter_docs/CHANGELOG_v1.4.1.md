# CHANGELOG v1.4.1

## v1.4.1-production-LAB38-LAB42B-zsuite-t0-clean

Baza: **v1.4-production-LAB38-LAB42B**.

Zachowane:
- LAB38 single;
- LAB42B dual open-file;
- LAB14/LAB20/LAB26/LAB30/LAB31/LAB32/LAB36 reguły body/raft/seam/pause/tower;
- zgodność z Z-Suite/open-file z v1.4.

Dodane/poprawione:
- potwierdzona fizycznie procedura dual `T1 -> T0` zgodna z natywnym Z-Suite;
- `RESTORE E0` po retrakcji starego toola `E -20`;
- T0 clean: `F480 E+21 area F4`, `F2000 E+22 area FE`, `DWELL 3000`, `0A -> 08 -> 09 -> 07 -> 0A -> 08 -> 00`, `F2000 E+21 area FD`, `RESTORE E0`;
- pomijanie najbliższego zdublowanego Orca `M109` po `ZORTRAX_TOOLCHANGE_CLEAN`;
- `LAYER_CLEAN T0` używa poprawionego T0 clean body, a `SKIP_AFTER_TOOLCHANGE=1` dalej chroni przed podwójnym purge.

Confirmed 2026-05-02 after physical test on cone_0.3_Z-PLA_Z-SUPPORT_28m3s_T0_EXACT_ZSUITE_CLEAN_RESTORE_TEST.zcode:
- Dual T1->T0 toolchange-clean must use native Z-Suite T0 dual profile, not single-like T0 start purge.
- After old T1 retract: E -20 area F3, immediately RESTORE E0.
- T0 clean body: POS00, F480 E+21.000 area F4, F2000 E+22.000 area FE, DWELL 3000,
  clean path 0A->08->09->07->0A->08->00, F2000 E+21.000 area FD, RESTORE E0.
- T1 remains as before: E -20 area E9 -> RESTORE E0, EA/FE/DWELL/T1 path/FD/RESTORE.
- Post-clean Orca M109 for the same tool is skipped after ZORTRAX_TOOLCHANGE_CLEAN to avoid duplicate wait/loading.
- LAYER_CLEAN for T0 uses the same corrected T0 clean body, without toolchange switch/retract.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
