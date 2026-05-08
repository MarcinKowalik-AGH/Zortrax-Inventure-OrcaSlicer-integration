# Layer clean DUAL smart restore

Fixes a real-print issue where `;ZORTRAX_LAYER_CLEAN DUAL ...` could select/clean T1 after the last support/tower use and leave the support head active at the final high layers.

Rules:
- DUAL layer-clean always cleans/restores the currently active tool.
- It cleans the other tool only if that tool is used later in the executable G-code.
- It restores the original active tool before returning to normal print moves.
- FULL_DUAL / DUAL_FULL / BOTH force cleaning both heads.
