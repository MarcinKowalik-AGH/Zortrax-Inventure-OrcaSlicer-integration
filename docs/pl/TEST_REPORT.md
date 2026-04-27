# Raport kontroli paczki v1.01

Kontrole wykonane przy przygotowaniu paczki GitHub:

- sprawdzono strukturę archiwum źródłowego `Zortrax_Inventure_Orca_v1.01.zip`,
- przeniesiono 6 plików źródłowych do układu repozytorium,
- sprawdzono integralność archiwów `.orca_printer` poleceniem `unzip -t`,
- sprawdzono składnię launcherów shellowych przez `bash -n`,
- potwierdzono, że główna paczka nie wymaga `g2z.jar` ani Javy,
- przygotowano dokumentację powiązań plików, markerów i metadanych Orca.

Zawartość źródła v1.01:

```text
g2z_wrapper_orca.py
run_g2z_orca_postprocess.bat
run_g2z_orca_postprocess.sh
run_g2z_orca_postprocess.command
Zortrax Inventure 0.4 nozzle - dual.orca_printer
Zortrax Inventure 0.4 nozzle - single.orca_printer
```
