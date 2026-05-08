# Z-Suite hints integration

This version parses an optional comment block exported by Orca:

```gcode
; ===== ZORTRAX ZSUITE HINTS BEGIN =====
; zsuite_profile_schema=1
; zsuite_retraction_before_change_to_model={retract_length_toolchange[1]}
; zsuite_retraction_before_change_to_model_speed={retraction_speed[1]}
; zsuite_retraction_before_change_to_support={retract_length_toolchange[0]}
; zsuite_retraction_before_change_to_support_speed={retraction_speed[0]}
; zsuite_purge_after_change_to_model=AUTO
; zsuite_purge_after_change_to_model_speed={deretraction_speed[0]}
; zsuite_purge_after_change_to_support=AUTO
; zsuite_purge_after_change_to_support_speed={deretraction_speed[1]}
; zsuite_sleep_time_before_brushing=3000
; zsuite_brushing_times=AUTO
; zsuite_extruder_switch_in_firmware=1
; zsuite_bin_clean_enabled=1
; zsuite_waste_tower_enable=AUTO
; zsuite_waste_tower_source=ORCA_PRIME_TOWER
; ===== ZORTRAX ZSUITE HINTS END =====
```

The hints are intentionally **diagnostic / semantic** by default.  They are parsed,
shown in logs/reports and used to confirm direction/model-support semantics, but
they do not override the confirmed byte-level clean profiles unless a future build
explicitly enables such policy.  This preserves the confirmed v1.4.2 single T0 clean
path and the confirmed dual T1->T0 clean path.

Key preserved rules:

- single T0 clean stays: `FE -> FE -> T0 brush path -> FD -> RESTORE E0`.
- single T0 clean must not use dual `area F4` or `DWELL 3000`.
- dual T1->T0 clean stays: `F4 -> FE -> DWELL -> T0 brush path -> FD -> RESTORE E0`.
- printed Orca prime/cooling tower remains separate from bin/waste purge-clean over the bucket.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
