# ZORTRAX_LOAD_FILAMENT — v1.4.16

Opcjonalny marker do świadomego wywołania skróconej, potwierdzonej na drukarce procedury load-like nad koszem. Domyślnie nie jest częścią START_MACHINE.

## Składnia

```gcode
;ZORTRAX_LOAD_FILAMENT T0
;ZORTRAX_LOAD_FILAMENT T1
;ZORTRAX_LOAD_FILAMENT BOTH
;ZORTRAX_LOAD_FILAMENT AUTO
```

Opcje:

```text
PARK=1/0          domyślnie 1; parkuje T0 na 09, T1 na 0A
POST_RESTORE=1/0  domyślnie 1; dodaje RESTORE E0 po parkowaniu
TEMP=AUTO/OFF     domyślnie AUTO; ustawia temperatury z Orca, OFF pomija temp commands
T0_TEMP=...       ręczny override T0
T1_TEMP=...       ręczny override T1
STANDBY_TEMP=...  ręczny override płytkiego standby inactive tool
```

## AUTO

- SINGLE -> T0
- DUAL -> T0 potem T1

## Ważne

Procedura celowo zachowuje potwierdzony trigger: po technicznej retrakcji -20 mm starego narzędzia nie ma natychmiastowego RESTORE E0. Na końcu procedury jest RESTORE, park i dodatkowy RESTORE po parkowaniu.

Nie stosować jako zamiennika normalnego TOOLCHANGE_CLEAN. To opcjonalny pre-print/load marker do ręcznego użycia.
