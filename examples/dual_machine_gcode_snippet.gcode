; DUAL — Zortrax Inventure / Orca v1.4.16
; Machine start G-code
;ZORTRAX_START_MACHINE DUAL CHAMBER=AUTO T0_TEMP=AUTO T1_TEMP=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO

; Change filament / Tool change G-code
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} direction_model_support={previous_extruder}->{next_extruder} zsuite_direction=AUTO layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO OOZE_PREVENTION=AUTO STANDBY_TEMP=AUTO PREHEAT_TIME=AUTO
M400

; Layer change G-code
G92 E0
;ZORTRAX_LAYER_CLEAN DUAL EVERY=20 START_LAYER=10 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO E_SPEED_SCALE=AUTO RETRACT_SPEED_SCALE=AUTO TEMP=AUTO
;ZORTRAX_LAYER_META layer_num={layer_num} layer_z={layer_z}

; Machine end G-code
;ZORTRAX_END_MACHINE AUTO
