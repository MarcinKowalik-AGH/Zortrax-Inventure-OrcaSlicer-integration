# Updating the GitHub repository from v1.01 to v1.4.16

## Git CLI workflow

```bash
git clone https://github.com/MarcinKowalik-AGH/Zortrax-Inventure-OrcaSlicer-integration.git
cd Zortrax-Inventure-OrcaSlicer-integration

git checkout -b release/v1.4.16

# copy this package content into the repository
# especially: converter/, orca_presets/, docs/, examples/, source_context/

git add .
git commit -m "Update Zortrax Inventure Orca integration to v1.4.16"
git push origin release/v1.4.16
```

Then open a Pull Request or merge the branch and create release `v1.4.16`.

## GitHub web workflow

1. Create branch `release/v1.4.16`.
2. Upload folders `converter/`, `orca_presets/`, `docs/`, `examples/`, `source_context/`.
3. Commit with message: `Update Zortrax Inventure Orca integration to v1.4.16`.
4. Create release `v1.4.16`.
5. You can add the original production ZIP as a release asset `Zortrax_Inventure_Orca_PRODUCTION_v1.4.16_converter_configs_2026-05-06.zip`.
