# Z-Suite automatrix / procedure compatibility

The converter does not use Z-Suite at runtime, but reproduces selected behavior confirmed from native files and tests.

Key markers:

```text
;ZORTRAX_START_MACHINE
;ZORTRAX_TOOLCHANGE_META
;ZORTRAX_TOOLCHANGE_CLEAN
;ZORTRAX_LAYER_CLEAN
;ZORTRAX_LAYER_META
;ZORTRAX_END_MACHINE
;ZORTRAX_LOAD_FILAMENT   optional, v1.4.16
```

Do not return to `g2z.jar` as normal runtime. Do not mix single T0 clean with dual T1→T0 clean.
