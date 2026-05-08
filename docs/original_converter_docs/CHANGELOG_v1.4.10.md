# v1.4.10 fan clamp / visible version fix

Hotfix for real Orca post-processing jobs.

## Fixed
- `M106 S...` fan values are now rounded/clamped to `0..255` before being encoded as classic ZCode B-axis fan command.
- Prevents `OverflowError: int too big to convert` in `pack_i32()` when Orca or a placeholder emits an unexpected huge fan S value.
- Updated visible base converter version string so logs no longer start with old `v1.4.2-base...` label.

## Not changed
- No confirmed LAB38/LAB42B motion logic changed.
- No purge/clean/toolchange semantics changed.
- ZSuite filament DB and OP02 speed semantics remain LOG_ONLY/metadata-driven as in v1.4.9.
