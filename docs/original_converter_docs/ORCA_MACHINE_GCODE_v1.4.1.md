# Orca Machine G-code — Zortrax Inventure v1.4.1

## SINGLE

Machine start:

```gcode
;ZORTRAX_START_MACHINE SINGLE E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5
```

Tool change: puste.

Layer change:

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

Machine end:

```gcode
;ZORTRAX_END_MACHINE AUTO
```

## DUAL

Machine start:

```gcode
;ZORTRAX_START_MACHINE DUAL E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5
```

Tool change / Change filament:

```gcode
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400
```

Layer change:

```gcode
G92 E0
;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=0.5 RETRACT_SPEED_SCALE=0.5 TEMP=AUTO
```

Machine end:

```gcode
;ZORTRAX_END_MACHINE AUTO
```


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
