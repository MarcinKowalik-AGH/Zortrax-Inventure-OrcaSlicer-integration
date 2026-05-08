#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pip install -r build/requirements-build.txt
python3 -m PyInstaller --clean --onedir --name g2z_wrapper_orca --add-data "converter/g2z_wrapper_orca_base_lab14_known_good.py:." converter/g2z_wrapper_orca.py
cp converter/g2z_wrapper_orca_base_lab14_known_good.py dist/g2z_wrapper_orca/g2z_wrapper_orca_base_lab14_known_good.py
echo "Built dist/g2z_wrapper_orca/g2z_wrapper_orca"
