# Reverse engineering notes

This project is based on analysis of Z-Suite files, `.zcode` files, Orca presets and physical printer tests.

Main findings:

- Normal runtime does not require Z-Suite or `g2z.jar`.
- Confirmed header fields include model material, support material, mode triplet, filament lengths and CRC.
- `byte72` is not a simple single/dual flag.
- `OP02` is feedrate-related; normal print speeds come from Process → G-code `F` → OP02.
- Bin purge/clean above the waste bin is not the same as the printed prime/cool/waste tower on the bed.
- Do not change motion solely from Z-Suite strings without `.zcode` samples and testing.
