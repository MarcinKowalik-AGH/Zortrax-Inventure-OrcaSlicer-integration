# Troubleshooting

## Orca does not create `.zcode`

- Check the post-processing script path.
- Check that both `.py` files are present in the OrcaScripts directory.
- Check `orca_postprocess_last.log` if it was created.

## Error after update

Most common cause: only `g2z_wrapper_orca.py` was replaced while the old base file remained.

## Single behaves like dual

- In single mode, Tool change / Change filament G-code must be empty.
- Do not add dual `TOOLCHANGE_CLEAN` to a single profile.

## Temperatures do not match Orca

- Use `CHAMBER=AUTO`, `T0_TEMP=AUTO`, `T1_TEMP=AUTO` in normal presets.
- Do not hard-code values like `CHAMBER=45` unless you intentionally want an override.

## Strange fan values

The converter clamps `M106 S` to `0..255`. If the error returns, an old converter is probably running.

## Z-SUPPORT ATP

`0x13` is experimental. Test carefully.
