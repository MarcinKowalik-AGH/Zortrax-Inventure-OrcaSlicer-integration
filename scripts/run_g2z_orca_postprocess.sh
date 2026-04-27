#!/usr/bin/env bash
set -u

LAUNCHER_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -n "${HOME:-}" ]]; then
  USER_HOME="$HOME"
else
  printf '[ERROR] Could not determine user home directory.\n'
  exit 1
fi

HOME_SCRIPTS="$USER_HOME/OrcaScripts"
if [[ -f "$HOME_SCRIPTS/g2z_wrapper_orca.py" ]]; then
  SCRIPT_DIR="$HOME_SCRIPTS"
  SCRIPT_SOURCE="home"
else
  SCRIPT_DIR="$LAUNCHER_DIR"
  SCRIPT_SOURCE="launcher"
fi

cd "$SCRIPT_DIR" || exit 1

WRAPPER="$SCRIPT_DIR/g2z_wrapper_orca.py"
LOGFILE="$SCRIPT_DIR/orca_postprocess.log"
INPUT="${1:-}"

printf '==========================================\n'
printf 'Zortrax Inventure - Orca post-process\n'
printf 'Converter : v1.01\n'
printf '==========================================\n'
printf 'User home : %s\n' "$USER_HOME"
printf 'Launcher  : %s\n' "$LAUNCHER_DIR"
printf 'Script dir: %s\n' "$SCRIPT_DIR"
printf 'Source    : %s\n' "$SCRIPT_SOURCE"
printf 'Wrapper   : %s\n' "$WRAPPER"
printf 'Log file  : %s\n' "$LOGFILE"
printf 'Input     : %s\n' "$INPUT"
printf '[INFO] Script location mode: prefer $HOME/OrcaScripts, then launcher directory.\n'
printf '[INFO] Output mode: Orca environment only. The converter writes to the final Save/Save As path provided by Orca.\n'
printf '[INFO] Progress mode: stable plain console output by default.\n\n'

if [[ -z "$INPUT" ]]; then
  printf '[ERROR] Missing input file from Orca.\n'
  exit 1
fi

if [[ ! -f "$WRAPPER" ]]; then
  printf '[ERROR] Wrapper not found: %s\n' "$WRAPPER"
  exit 1
fi

find_python() {
  if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
    PYTHON_EXE="$PYTHON_BIN"
    return 0
  fi
  local candidates=(
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "/opt/homebrew/bin/python"
    "/usr/local/bin/python"
    "/usr/bin/python3"
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -x "$c" ]]; then
      PYTHON_EXE="$c"
      return 0
    fi
  done
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="$(command -v python3)"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    PYTHON_EXE="$(command -v python)"
    return 0
  fi
  return 1
}

if ! find_python; then
  printf '[ERROR] Python was not found on this system.\n'
  exit 1
fi

if [[ -z "${G2Z_PROGRESS_STYLE:-}" ]]; then
  export G2Z_PROGRESS_STYLE="plain"
fi
export PYTHONUNBUFFERED=1
export G2Z_LOG_FILE="$LOGFILE"

printf '[INFO] Python    : %s -u\n' "$PYTHON_EXE"
printf '[START] Launching converter...\n\n'

"$PYTHON_EXE" -u "$WRAPPER" "$INPUT" --log
ERR=$?

printf '\n'
if [[ "$ERR" -ne 0 ]]; then
  printf '[ERROR] Converter exited with code %s.\n' "$ERR"
  printf '[INFO] See log: %s\n' "$LOGFILE"
  exit "$ERR"
fi

printf '[OK] Conversion finished successfully.\n'
printf '[INFO] Log: %s\n' "$LOGFILE"
exit 0
