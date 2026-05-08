# Build / kompilacja wrappera v1.4.1

Kompilacja jest opcjonalna. Zalecana praca z Orca używa zwykłych plików Python z katalogu `converter/`.

## Windows

Uruchom:

```bat
build\build_pyinstaller_windows.bat
```

Wynik: `dist\g2z_wrapper_orca\g2z_wrapper_orca.exe`.

## macOS / Linux

Uruchom:

```bash
bash build/build_pyinstaller_macos_linux.sh
```

Wynik: `dist/g2z_wrapper_orca/g2z_wrapper_orca`.

## Ważne

Plik `g2z_wrapper_orca_base_lab14_known_good.py` musi znajdować się obok wrappera albo obok skompilowanego programu. Wrapper v1.4 zachowuje tę zależność celowo, żeby nie ukrywać bazy LAB14/v1.2.7 wewnątrz binarki.


## v1.4.9 / v1.2.14 filament DB note
Adds Inventure-oriented filament database documentation, `ZORTRAX_FILAMENT_PROFILE` comment audit support, native Z-ABS, native Z-PEEK placeholder, and experimental Z-SUPPORT ATP 0x13 from zcodex2. Motion generation remains governed by confirmed ZORTRAX_* markers.
