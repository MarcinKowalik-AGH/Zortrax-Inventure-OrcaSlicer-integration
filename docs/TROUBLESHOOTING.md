# Diagnostyka

## Orca nie tworzy `.zcode`

Sprawdź:

1. Czy w Orca podano pełną ścieżkę do launchera post-processingu.
2. Czy `scripts/g2z_wrapper_orca.py` znajduje się w `~/OrcaScripts` / `%USERPROFILE%\OrcaScripts` albo w tym samym katalogu co launcher.
3. Czy Python 3 jest dostępny.
4. Czy powstał log:
   - Windows: `orca_postprocess_last.log`,
   - macOS: `orca_postprocess.log`.

## Błąd: Orca output path is not available

Dla plików `.gcode.pp` konwerter wymaga finalnej ścieżki Save/Save As od Orca. Jeżeli jej nie ma, kończy pracę błędem. To jest celowe: v1.01 nie zapisuje już wyników do starego katalogu `out`.

Możliwe obejście diagnostyczne:

```bash
python3 scripts/g2z_wrapper_orca.py -i input.gcode -o output.zcode --log
```

## Drukarka robi nieoczekiwany homing

W presetach należy używać markera:

```gcode
;ZORTRAX_START_MACHINE AUTO
```

W v1.01 gołe `G28` w konwerterze zostało zabezpieczone tak, aby emitowało rozdzielone homing XY oraz Z, ale integracja Orca powinna nadal opierać się na `ZORTRAX_START_MACHINE`, bo marker emituje całą sekwencję startową Z-Suite-like.

## Błąd materiału na drukarce

Najpierw sprawdź:

- czy `filament_t0` i `filament_t1` w metadanych odpowiadają realnym materiałom,
- czy materiał T1 jest supportem, jeżeli wydruk jest dual,
- czy mapping materiałów w `g2z_wrapper_orca.py` zawiera daną nazwę,
- czy support Z-SUPPORT family wymaga tripletu `01 03 00`, a BASF BVOH `01 02 01`.

## `PURGE=AUTO` nic nie robi

`PURGE=AUTO` w toolchange zależy od metadanych Orca, zwłaszcza `flush_length`. Jeżeli Orca wyliczy `flush_length=0`, purge może zostać pominięty.

Start purge jest niezależny od `flush_length` i bierze ilość z `LENGTH=...`:

```gcode
;ZORTRAX_START_PURGE DUAL LENGTH=30
```

## macOS nie pokazuje okna Terminal

To jest oczekiwane. Aktualna decyzja projektowa: macOS może działać cicho w tle, a diagnostyka odbywa się przez log.
