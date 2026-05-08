# Troubleshooting — PL

## Orca nie tworzy `.zcode`

- Sprawdź ścieżkę do post-process script.
- Sprawdź, czy w katalogu OrcaScripts są oba pliki `.py`.
- Sprawdź log `orca_postprocess_last.log`, jeśli powstał.

## Błąd po aktualizacji

Najczęstsza przyczyna: podmieniono tylko `g2z_wrapper_orca.py`, ale został stary `g2z_wrapper_orca_base_lab14_known_good.py`.

## Single zachowuje się jak dual

- W single sekcja Tool change / Change filament musi być pusta.
- Nie dodawać dualowego `TOOLCHANGE_CLEAN` do profilu single.

## Temperatury nie są takie jak w Orca

- W normalnych presetach używać `CHAMBER=AUTO`, `T0_TEMP=AUTO`, `T1_TEMP=AUTO`.
- Nie wpisywać twardych wartości typu `CHAMBER=45`, jeśli nie chcesz wymusić override.

## Dziwne wartości wentylatora

Konwerter zawiera clamp `M106 S` do `0..255`. Jeśli błąd wraca, prawdopodobnie uruchamia się stara wersja konwertera.

## Z-SUPPORT ATP

`0x13` jest wpisem eksperymentalnym. Testować ostrożnie.
