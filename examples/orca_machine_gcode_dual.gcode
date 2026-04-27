; ===== Zortrax Inventure dual start/toolchange/end example =====

; Machine start G-code
;ZORTRAX_START_MACHINE AUTO
;ZORTRAX_START_PURGE DUAL LENGTH=30

; Layer change G-code
G92 E0

; Change filament / Tool change G-code
M400
;ZORTRAX_TOOLCHANGE_META previous_extruder={previous_extruder} next_extruder={next_extruder} layer_num={layer_num} layer_z={layer_z} toolchange_count={toolchange_count} old_temp={old_filament_temp} new_temp={new_filament_temp} old_retract={old_retract_length_toolchange} new_retract={new_retract_length_toolchange} old_e_f={old_filament_e_feedrate} new_e_f={new_filament_e_feedrate} flush_length={flush_length} first_flush_volume={first_flush_volume} second_flush_volume={second_flush_volume} flush_length_1={flush_length_1} flush_length_2={flush_length_2} flush_length_3={flush_length_3} flush_length_4={flush_length_4} x_after_toolchange={x_after_toolchange} y_after_toolchange={y_after_toolchange} z_after_toolchange={z_after_toolchange}
;ZORTRAX_SPECIAL_CLEAN AUTO 5 PURGE=AUTO IDLE_RETRACT=AUTO
M400

; Machine end G-code
;ZORTRAX_END_MACHINE AUTO
