# v1.4.8 OP02 speed semantics

- Adds LOG_ONLY Z-Suite OP02/feedrate area semantics from all native project samples and b1/b3 scaling comparison.
- Documents support-speed-controlled areas 0x04/0x05/0x18 and support-surface/interface areas 0x1B/0x21.
- Keeps converter byte streams and confirmed LAB38/LAB42B behavior unchanged.
- PETG-based classic .zcode material code remains 0x83.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
