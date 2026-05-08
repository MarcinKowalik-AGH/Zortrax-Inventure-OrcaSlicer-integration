#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/run_g2z_orca_postprocess.sh" "$@"
