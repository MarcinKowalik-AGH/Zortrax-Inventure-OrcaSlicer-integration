#!/usr/bin/env bash
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# SPDX-License-Identifier: MIT
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/run_g2z_orca_postprocess.sh" "$@"
