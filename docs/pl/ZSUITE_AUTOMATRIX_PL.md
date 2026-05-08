# Z-Suite automatrix / zgodność z procedurami

Konwerter nie używa Z-Suite w runtime, ale odtwarza wybrane zachowania potwierdzone z natywnych plików i testów.

Kluczowe markery:

```text
;ZORTRAX_START_MACHINE
;ZORTRAX_TOOLCHANGE_META
;ZORTRAX_TOOLCHANGE_CLEAN
;ZORTRAX_LAYER_CLEAN
;ZORTRAX_LAYER_META
;ZORTRAX_END_MACHINE
;ZORTRAX_LOAD_FILAMENT   opcjonalny, v1.4.16
```

Nie wracać do `g2z.jar` jako normalnego runtime. Nie mieszać single T0 clean z dualowym T1→T0 clean.
