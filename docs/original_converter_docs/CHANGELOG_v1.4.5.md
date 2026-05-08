# v1.4.5 — macOS Python 3.9 bit_count compatibility hotfix

Problem observed in Orca post-processing on macOS:

```text
AttributeError: 'int' object has no attribute 'bit_count'
```

Cause: `/usr/bin/python3` on some macOS systems does not provide `int.bit_count()`, while the v1.4.4 wrapper used it in the local `pop()` helper.

Fix:
- replaced direct `int(x).bit_count()` with a compatibility fallback using Kernighan popcount loop,
- no change to confirmed LAB38/LAB42B semantics,
- no change to Z-Suite hints policy (`LOG_ONLY`),
- no change to single T0 clean / dual T0 toolchange clean generation.

Validation:
- `python3 -m py_compile converter/g2z_wrapper_orca.py` OK,
- LAB38 single byte-for-byte self-check remains OK.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
