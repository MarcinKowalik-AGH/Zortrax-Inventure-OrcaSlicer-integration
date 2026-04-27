#!/usr/bin/env bash
# Converter: v1.01
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec /bin/bash "$SCRIPT_DIR/run_g2z_orca_postprocess.sh" "$@"
