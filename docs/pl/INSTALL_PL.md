# Instalacja — Windows i macOS

## 1. Import presetów Orca

W OrcaSlicer zaimportuj aktualny preset z katalogu:

```text
orca_presets/
```

Najważniejsze pliki:

```text
Zortrax Inventure 0.4 nozzle - single_v1.4.14_current_converter.orca_printer
Zortrax Inventure 0.4 nozzle - dual_v1.4.14_current_converter.orca_printer
```

Można też użyć zbiorczego ZIP-a presetów, jeśli Orca poprawnie go importuje.

## 2. Instalacja konwertera

Skopiuj wszystkie pliki z `converter/` do katalogu skryptów Orca.

### Windows

Zalecany katalog:

```text
C:\Users\<USER>\OrcaScripts\
```

Przykład:

```text
C:\Users\Marcin Kowalik\OrcaScripts\
```

Skopiuj:

```text
g2z_wrapper_orca.py
g2z_wrapper_orca_base_lab14_known_good.py
run_g2z_orca_postprocess.bat
```

W OrcaSlicer → Printer settings → Others → Post-processing scripts wpisz:

```text
C:\Users\<USER>\OrcaScripts\run_g2z_orca_postprocess.bat
```

### macOS

Zalecany katalog:

```text
/Users/<username>/OrcaScripts/
```

Polecenia:

```bash
mkdir -p ~/OrcaScripts
cp converter/* ~/OrcaScripts/
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.sh
chmod +x ~/OrcaScripts/run_g2z_orca_postprocess.command
```

W OrcaSlicer → Printer settings → Others → Post-processing scripts wpisz:

```text
/Users/<username>/OrcaScripts/run_g2z_orca_postprocess.command
```

## 3. Krytyczna zasada aktualizacji

Zawsze podmieniaj jednocześnie:

```text
g2z_wrapper_orca.py
g2z_wrapper_orca_base_lab14_known_good.py
```

Nie mieszać starego wrappera z nowym plikiem bazowym ani odwrotnie.

## 4. Pierwszy test

1. Wybierz prosty mały model.
2. Użyj profilu single lub dual z paczki.
3. Wygeneruj plik przez Orca post-process.
4. Sprawdź, czy powstał `.zcode`.
5. Najpierw wykonaj krótki wydruk kontrolny.
