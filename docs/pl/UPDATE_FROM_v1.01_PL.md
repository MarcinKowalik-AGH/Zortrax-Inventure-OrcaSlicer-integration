# Aktualizacja repozytorium GitHub z v1.01 do v1.4.16

## Wariant git CLI

```bash
git clone https://github.com/MarcinKowalik-AGH/Zortrax-Inventure-OrcaSlicer-integration.git
cd Zortrax-Inventure-OrcaSlicer-integration

git checkout -b release/v1.4.16

# skopiuj zawartość tej paczki do repozytorium
# w szczególności: converter/, orca_presets/, docs/, examples/, source_context/

git add .
git commit -m "Update Zortrax Inventure Orca integration to v1.4.16"
git push origin release/v1.4.16
```

Następnie utwórz Pull Request lub zmerguj branch i utwórz release `v1.4.16`.

## Wariant przez GitHub web

1. Utwórz branch `release/v1.4.16`.
2. Wgraj foldery `converter/`, `orca_presets/`, `docs/`, `examples/`, `source_context/`.
3. Zatwierdź commit: `Update Zortrax Inventure Orca integration to v1.4.16`.
4. Utwórz release `v1.4.16`.
5. Jako release asset można dodać oryginalny ZIP produkcyjny `Zortrax_Inventure_Orca_PRODUCTION_v1.4.16_converter_configs_2026-05-06.zip`.
