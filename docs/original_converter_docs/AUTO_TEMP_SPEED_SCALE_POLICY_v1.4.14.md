# AUTO temperature and speed-scale policy — v1.4.14

Recommended marker style:

```gcode
;ZORTRAX_START_MACHINE DUAL CHAMBER=AUTO T0_TEMP=AUTO T1_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
;ZORTRAX_LAYER_CLEAN DUAL EVERY=20 START_LAYER=10 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
```

Temperature priority:

1. explicit numeric marker override, for example `T0_TEMP=215` or `CHAMBER=45`;
2. current values emitted by Orca metadata / G-code after user edits;
3. Z-Suite material/pair defaults in converter DB;
4. fallback.

`AUTO` for temperatures allows Orca-edited values to pass through; it does not lock the Z-Suite default.

Speed-scale scope:

`E_SPEED_SCALE` and `RETRACT_SPEED_SCALE` apply only to converter-generated technical Zortrax procedures: `START_MACHINE`, `START_PURGE`, `TOOLCHANGE_CLEAN`, and `LAYER_CLEAN`. They do not change normal print/process speeds such as outer wall, inner wall, infill, support, tower, raft or travel. Normal print speed remains `Process -> G-code F -> ZCode OP02`.

AUTO speed-scale map:

- support / BVOH / PVA / Z-SUPPORT family: `0.6`;
- FLEX / SEMIFLEX: `0.8`;
- normal model materials: `1.0`.

Explicit numeric values still win, for example `E_SPEED_SCALE=0.4`.
