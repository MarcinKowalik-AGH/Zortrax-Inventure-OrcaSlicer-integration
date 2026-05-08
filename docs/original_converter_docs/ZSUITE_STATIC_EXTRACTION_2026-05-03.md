# Z-Suite static extraction — 2026-05-03

Zakres: statyczna analiza paczki `Z-Suite.zip` dostarczonej przez użytkownika. Program nie był uruchamiany; wykonano tylko analizę offline plików, stringów i zasobów `.NET`.

## Co znaleziono

### Struktura aplikacji

Paczka zawiera m.in.:

- `Z-SUITE.exe`
- `Z-SUITE.dll` — główna aplikacja .NET / WPF
- `ZortraxNativeWrapper.dll`
- `ZortraxNativeWrapperClassic.dll`
- zasoby CefSharp / Chromium
- `Profiles/default mode.zprof`

`Z-SUITE.dll` jest głównym źródłem nazw klas, pól i zasobów. `ZortraxNativeWrapperClassic.dll` zawiera mało czytelnych stringów i nie ujawnił bezpośrednio kompletnej tabeli opcode classic `.zcode`.

## Najważniejsze nazwy wewnętrzne Z-Suite przydatne dla konwertera

W `Z-SUITE.dll` znaleziono klasyczne pola konfiguracji związane z toolchange / purge / tower:

```text
ES_RetractionBeforeChangeToModel
ES_RetractionBeforeChangeToModelSpeed
ES_RetractionBeforeChangeToSupport
ES_RetractionBeforeChangeToSupportSpeed
ES_PurgeAfterChangeToModel
ES_PurgeAfterChangeToModelSpeed
ES_PurgeAfterChangeToSupport
ES_PurgeAfterChangeToSupportSpeed
ES_SleepTimeBeforeBrusning
ES_BrushingTimes
ES_ExtruderSwitchInFirmware
ES_WasteTowerEnable
ES_WasteTowerSizeX
ES_WasteTowerSizeY
ES_WasteTowerCenterX
ES_WasteTowerCenterY
ES_WasteTowerOffset
ES_WasteTowerSpeedModel
ES_WasteTowerSpeedSupport
ES_WasteTowerFeedModel
ES_WasteTowerFeedSupport
```

Dodatkowo znaleziono pola istotne dla profili Inventure/support:

```text
InventureBackFanSpeed
SupportTempExtruder
LowTempSupport
WarmingTimeFromLowTempSupport
WarmingMarginTimeFromLowTempSupport
StartGCode
EndGCode
EnableRaft
EnableSupport
```

## Z-Suite UI printer enum

W zasobach UI znaleziono enum używany przez Z-Suite do identyfikacji modeli drukarek w interfejsie:

```text
M200        = 0
Inventure   = 1
M350        = 2
M300PL      = 3
M300CN      = 4
M200Plus    = 5
M300Plus    = 6
Inkspire    = 7
M300Dual    = 8
Apoller     = 9
Endureal    = 11
Inkspire2   = 12
CustomResin = 250
```

Bardzo ważne: to jest enum UI Z-Suite, nie bajt `header[61]` w classic `.zcode`. Aktualny konwerter nadal zachowuje potwierdzony `header[61] = 0x0A` dla Inventure. Nie wolno zamienić tego na `1` bez osobnego testu na drukarce i natywnych plikach.

## Co dodano w v1.4.3

Dodano bezpieczną, log-only warstwę diagnostyczną:

- stałą `ZSUITE_UI_PRINTER_MODEL_IDS`, oddzieloną od classic `.zcode` header device id,
- słownik `ZSUITE_CLASSIC_CONFIG_KEYS` z nazwami Z-Suite jako aliasami diagnostycznymi,
- audyt po konwersji:
  - raportuje `ui_printer_model_id(Inventure)=1`,
  - raportuje rzeczywisty `zcode_header_device_id`,
  - dla single wykrywa regresję typu dual T0 clean w single, czyli obecność `area F4` i/lub `DWELL 3000`.

Audyt niczego nie zmienia w `.zcode`; tylko ostrzega w konsoli/logu.

## Co można dodać później

1. W logach mapować nasze opcje na nazwy Z-Suite, np. `IDLE_RETRACT` ↔ `ES_RetractionBeforeChangeToModel/Support`.
2. Rozbudować bazę tower o pola `ES_WasteTower*`, ale tylko po porównaniu z natywnymi `.zcode` dla tych samych modeli.
3. Dodać osobny raport `--zsuite-diagnostics`, jeśli potrzebne będzie pełniejsze porównanie z terminologią Z-Suite.

## Czego NIE dodawać automatycznie

- Nie zmieniać `header[61]` na `1`; `1` to ID UI, a nie potwierdzony bajt classic `.zcode`.
- Nie przepisywać algorytmu preview/command stream z nazw stringów bez testów.
- Nie traktować `ES_WasteTower*` jako binarnej definicji obszarów `0x1D/0x1E` bez natywnych par porównawczych.
- Nie mieszać drukowanej prime/cool tower na stole z purge/clean nad pojemnikiem.

## Status

Najbardziej wartościowy bezpieczny zysk z Z-Suite na teraz to nazewnictwo, enum UI i diagnostyka regresji. Nie znaleziono jawnej kompletnej tabeli classic opcode ani bezpośrednich danych, które można bez testów zamienić na nowe ruchy w konwerterze.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
