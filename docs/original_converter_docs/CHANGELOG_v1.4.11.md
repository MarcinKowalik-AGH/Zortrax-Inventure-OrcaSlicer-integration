# v1.4.11 — Orca temperature overrides Z-Suite defaults

- Z-Suite filament/profile DB temperatures are now treated as defaults only.
- ORCA METADATA and manual START_MACHINE options can override temperatures for the current print.
- Added START_MACHINE manual overrides: `CHAMBER=`, `CHAMBER_TEMP=`, `BED_TEMP=`, `T0_TEMP=`, `MODEL_TEMP=`, `T1_TEMP=`, `SUPPORT_TEMP=`.
- Pre-START_MACHINE Orca heating commands (`M104`, `M109`, `M140`, `M141`, `M190`, `M191`) are skipped when `;ZORTRAX_START_MACHINE` exists later in the file. This prevents old Orca bed/chamber waits from fighting the Zortrax start sequence.
- In dual jobs, conflicting T0/T1 bed/chamber metadata is treated as ambiguous and falls back to the Z-Suite pair default unless an explicit job-level chamber override is provided.
- Fan clamp from the previous hotfix is preserved.
