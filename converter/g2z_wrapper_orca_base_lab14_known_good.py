
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

SCRIPT_VERSION = "v1.4.16-base-LAB38-safe-load-filament-marker-2026-05-06"
SCRIPT_CHANGELOG = [
    "profile-suffix-policy: allow user suffixes after canonical filament/process/printer preset names, e.g. Z-PLA test, 0.15mm Quality ... test, Zortrax Inventure ... test; canonical prefix is used for mapping and logs.",
    "v1.4.10-fan-clamp-version-fix: clamp/round M106 S fan values to 0..255 before encoding B axis to prevent i32 overflow from Orca/placeholder fan commands; update visible base version string.",
    "v1.4.1 material-db update: latest Z-Suite material codes/profiles, E+F+area purge database, native Z-ABS 0x00, external PETG 0x83/FLEX 0x87, SEMIFLEX 0x96; preserve LAB14/LAB20/LAB26/LAB32/LAB38/LAB42B and confirmed T0 clean fix.",
    "v1.4.1-base-zsuite-t0-clean: confirmed Z-Suite dual T0 clean profile; restore E after old-tool retract; skip duplicate post-clean Orca M109; keep SKIP_AFTER_TOOLCHANGE for layer clean.",
    "v1.3-beta/LAB14: connector semantics; pure-E -> retract/deretract, XY no-E -> JUMP_PATH, long low-E connectors -> JUMP_PATH, short top low-E -> SEAM; preserves v1.2.7 and LAB09 open-file fixes.",
    "LAB09: integrate confirmed LAB08 T02/TP02 open-preview fix: byte72=0 for no-raft viewer class, report-progress 0x0B one-byte payload, ignore M110 as non-layer, map excessive first-layer support area 0x18 to SUPPORT_INFILL for Orca no-raft output.",
    "v1.2.7-e-speed-scale: add common E_SPEED_SCALE and RETRACT_SPEED_SCALE marker options for START_MACHINE, TOOLCHANGE_CLEAN, LAYER_CLEAN and START_PURGE.",
    "v1.2.6-layer-clean-skip-after-toolchange: add SKIP_AFTER_TOOLCHANGE for ;ZORTRAX_LAYER_CLEAN so periodic clean does not immediately repeat purge after ;ZORTRAX_TOOLCHANGE_CLEAN.",
    "v1.2.5-layer-clean-start-layer: add START_LAYER/MIN_LAYER/SKIP_FIRST for ;ZORTRAX_LAYER_CLEAN so first printed layer can be skipped after START_MACHINE purge.",
    "v1.2.3-temp-ooze-clean: set Orca material temperatures before START_MACHINE/TOOLCHANGE_CLEAN/LAYER_CLEAN purge and restore ooze-prevention standby/preheat handling for inactive tools.",
    "v1.2.4-quiet-progress-preheat-fix: move repetitive temp/ooze/profile diagnostics to log-only output by default and fix PREHEAT_TIME=AUTO so it reads Orca preheat_time instead of displaying -1s.",
    "v1.2.2-dual-clean-markers: split cleaning into ;ZORTRAX_TOOLCHANGE_CLEAN for Change filament G-code and ;ZORTRAX_LAYER_CLEAN for Layer change G-code; both reuse Z-Suite-like switch/center/purge/clean subprocedures.",
    "v1.2.2-zsuite-special-clean: SPECIAL_CLEAN uses Z-Suite-like T0/T1 toolchange paths, material-based purge/prime profiles, and -20 mm idle retract AUTO.",
    "v1.2.1-zsuite-start-machine: START_MACHINE composes explicit/firmware Z-Suite start subprocedures separately for SINGLE and DUAL, with material-based FW/start-E profiles and averaged fallbacks.",
    "v1.02-start-e-profiles: START_MACHINE chooses Z-Suite start E-move lengths from detected materials; unknown materials use averaged fallback values from Z-Suite references.",
    "OK reference: START_PURGE length-only, no retract; heat selected tool from material metadata before purge.",
    "v1.20: Rebuild Orca configs from uploaded source bundles while preserving all process/filament presets.",
    "v1.19: START_PURGE forces drop zone and uses Orca retraction/deretraction speeds automatically.",
    "v1.18: Add ;ZORTRAX_START_PURGE AUTO LENGTH=60 RETRACT=5 with heated T0/T1 start purge.",
    "Added ;ZORTRAX_SPECIAL_CLEAN markers for Z-Suite-like head cleaning.",
    "Added ;ZORTRAX_SPECIAL_POS marker for direct MoveToSpecialPosition emission.",
    "Version is printed in console and written to log at startup.",
    "Added ;ZORTRAX_START_MACHINE markers using Z-Suite-like start-machine command sequences.",
    "Added ;ZORTRAX_END_MACHINE markers using Z-Suite-like end-machine command sequences.",
    "v3: After standalone cleaning markers, restore Z-Suite-like return feedrate before the next travel/print move.",
    "v4: Clamp the first post-clean XY travel move to Z-Suite-like return feedrate, even if Orca emits a slower F value.",
    "v5: Update converter active-tool state after Z-Suite embedded start/clean sequences and skip redundant T0/T1 toolchange blocks.",
    "v6: Track cleaned tools separately from active tool; defer AUTO/DUAL clean markers placed before Orca T0/T1 so the next tool is cleaned only on first use.",
    "v7: Fix real Orca toolchange behavior: SPECIAL_CLEAN AUTO now forces cleaning on every toolchange marker and no longer gets suppressed by cleaned_tools.",
    "v8: Add optional layer interval to ;ZORTRAX_SPECIAL_CLEAN, e.g. AUTO 10 cleans only on every 10th layer.",
    "v9: Fix slow return on skipped-clean toolchanges by restoring travel feedrate after every real T0/T1 switch.",
    "v5: Extend Z-Suite dual start-machine trailer with the planner/feedrate restore commands observed after final GarbageCenter in the same-STL Z-Suite reference.",
    "Changed SINGLE/DUAL clean markers to emit full Z-Suite-like speed/position/tool cleaning sequences.",
    "v11: ;ZORTRAX_SPECIAL_CLEAN DUAL N now means full two-head clean every N layers; DUAL is no longer deferred into a single-tool clean before T0/T1.",
    "v1.02: Add optional PURGE / PURGE=<mm> / PURGE_F=<feedrate> parameters to ZORTRAX_SPECIAL_CLEAN markers.",
    "v1.03: Print converter version immediately in terminal launchers and at Python startup.",
    "v1.04: Add optional IDLE_RETRACT=<mm> / IDLE_RETRACT_F=<feedrate> for inactive-tool retract and active-tool unretract on toolchange.",
    "v1.05: Final documented test package; no logic change from v1.04, includes full transfer notes for continuing opcode reverse engineering.",
    "v1.06: Read Orca retraction_speed/deretraction_speed metadata and auto-fill PURGE_F / IDLE_RETRACT_F when omitted.",
    "v1.10: Read extended Orca placeholders from file_start_gcode and ZORTRAX_TOOLCHANGE_META; fixed real single/dual Orca 2.3.2 configs.",
]


_LOG_FILE_PATH: Path | None = None

def set_log_file(path: str | Path | None) -> None:
    global _LOG_FILE_PATH
    if not path:
        _LOG_FILE_PATH = None
        return
    try:
        lp = Path(path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_text('', encoding='utf-8')
        _LOG_FILE_PATH = lp
    except Exception:
        _LOG_FILE_PATH = None

def _strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)

def _append_log_line(text: str) -> None:
    if _LOG_FILE_PATH is None:
        return
    try:
        with _LOG_FILE_PATH.open('a', encoding='utf-8', newline='\n') as f:
            f.write(_strip_ansi(text).rstrip('\r\n') + '\n')
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Confirmed Inventure header offsets from project findings.
# ---------------------------------------------------------------------------

HEADER_MAGIC = b"ZCode"
HEADER_MIN_LEN = 128
OFFSET_PRINT_TIME = 54
OFFSET_FW_TRIPLET = 58
OFFSET_DEVICE_ID = 61
OFFSET_MODEL_MATERIAL = 62
OFFSET_LAYER = 63
OFFSET_QUALITY = 64
OFFSET_INFILL = 65
OFFSET_SUPPORT_ANGLE = 66
OFFSET_SOFTWARE_VERSION = 68
OFFSET_MODEL_LENGTH_MM = 73
OFFSET_SUPPORT_LENGTH_MM = 77
OFFSET_SUPPORT_MATERIAL = 85
OFFSET_HEADER_CRC = 127

DEVICE_IDS = {
    "INVENTURE": 0x0A,
}

# Steps/mm for the classic Inventure path used by the current converter.
STEPS = {
    "X": 640,
    "Y": 640,
    "Z": 802,
    "E": 960,
    "A": 1,
    "B": 1,
    "Z2": 0,
}

UNKNOWN_PRINTING_AREA = 0xFF

# LAB05: ZTool/Z-Suite PrintingArea enum values extracted from ZTool.
# Used only for experimental Z-Suite preview/open-file tests.
AREA_MODEL_CONTOUR = 0x00
AREA_VISIBLE_INFILL = 0x01
AREA_MODEL_INVISIBLE_CONTOUR = 0x02
AREA_INVISIBLE_INFILL = 0x03
AREA_SUPPORT_CONTOUR = 0x04
AREA_SUPPORT_INFILL = 0x05
AREA_SUPPORT_INTERFACE_CONTOUR = 0x06
AREA_SUPPORT_INTERFACE_INFILL = 0x07
AREA_RAFT = 0x0A
AREA_RAFT_BOTTOM = 0x0B
AREA_RAFT_TRANSITION = 0x0C
AREA_RAFT_INTERFACE = 0x0D
AREA_VISIBLE_TOP_INFILL = 0x0E
AREA_VISIBLE_BOTTOM_INFILL = 0x0F
AREA_MODEL_CONTOUR_ENTRANCE = 0x14
AREA_MODEL_CONTOUR_EXIT = 0x15
AREA_FIRST_LAYER_MODEL_CONTOUR = 0x16
AREA_FIRST_LAYER_MODEL_FILL = 0x17
AREA_FIRST_LAYER_SUPPORT = 0x18
AREA_BRIDGE_INFILL = 0x19
AREA_BRIDGE_INFILL_CONTOUR = 0x1A
AREA_WASTE_TOWER_MODEL = 0x1D
AREA_WASTE_TOWER_SUPPORT = 0x1E
AREA_WASTE_TOWER_RAFT = 0x1F
AREA_SUPPORT_BOTTOM_INFILL = 0x20
# v1.3-beta / LAB14 connector semantics values from ZTool/Z-Suite PrintingArea enum.
AREA_SEAM = 0xDF
AREA_JUMP_PATH = 0xFB
AREA_JUMP = 0xFC
AREA_RETRACTION_BACK = 0xFD
AREA_RETRACTION_FORWARD = 0xFE

# Conservative thresholds used only for Z-Suite viewer classification.
# They do not alter movement coordinates or physical extrusion values.
LAB14_LOW_E_PER_MM = Decimal("0.006")
LAB14_LONG_CONNECTOR_MM = Decimal("8.0")
LAB14_SHORT_TOP_CONNECTOR_MM = Decimal("6.0")

MATERIAL_CODE_MAP = {
    # Native Zortrax
    "Z-ABS": 0x00,  # observed legacy/native Z-ABS in Z-Suite classic .zcode
    "Z-ULTRAT": 0x01,
    "Z-GLASS": 0x02,
    "Z-HIPS": 0x03,
    "Z-PCABS": 0x04,
    "Z-PETG": 0x05,
    "Z-ULTRAT PLUS": 0x06,
    "Z-SUPPORT": 0x07,
    "Z-ESD": 0x08,
    "Z-PHA": 0x09,
    "Z-PLA": 0x0A,
    "Z-PLA PRO": 0x0B,
    "Z-ASA PRO": 0x0C,
    "Z-SUPPORT PLUS": 0x0D,
    "Z-SEMIFLEX": 0x0E,
    "Z-FLEX": 0x0F,
    "Z-NYLON": 0x10,
    "Z-SUPPORT PREMIUM": 0x11,
    "Z-PEEK": 0x12,
    "Z-SUPPORT ATP": 0x13,  # experimental: observed in M300 Dual .zcodex2, not yet confirmed for Inventure classic/RFID
    # Support / open material map from project findings
    "BASF ULTRAFUSE BVOH": 0x17,
    "ABS-BASED FILAMENT": 0x81,
    "GLASS-TYPE FILAMENT": 0x84,
    # Header .zcode codes confirmed from native Z-Suite samples, 2026-05-03.
    "PETG-BASED FILAMENT": 0x83,
    "GLASS-TYPE FILAMENT": 0x84,
    "PLA-BASED FILAMENT": 0x86,
    "FLEX-BASED FILAMENT": 0x87,
    "NYLON-BASED FILAMENT": 0x89,
    "ULTRAT-BASED FILAMENT": 0x91,
    "ESD PETG-BASED FILAMENT": 0x92,
    "PLA PRO-BASED FILAMENT": 0x94,
    "ASA PRO-BASED FILAMENT": 0x95,
    "SEMIFLEX-BASED FILAMENT": 0x96,
}

MATERIAL_ALIASES = {
    "Z ABS": "Z-ABS",
    "Z-ABS": "Z-ABS",
    "Z ULTRAT PLUS": "Z-ULTRAT PLUS",
    "Z SUPPORT": "Z-SUPPORT",
    "Z SUPPORT PLUS": "Z-SUPPORT PLUS",
    "Z SUPPORT PREMIUM": "Z-SUPPORT PREMIUM",
    "Z SUPPORT ATP": "Z-SUPPORT ATP",
    "Z-SUPPORT ATP": "Z-SUPPORT ATP",
    "Z PLA": "Z-PLA",
    "Z PLA PRO": "Z-PLA PRO",
    "Z ASA PRO": "Z-ASA PRO",
    "Z PETG": "Z-PETG",
    "Z GLASS": "Z-GLASS",
    "Z SEMIFLEX": "Z-SEMIFLEX",
    "Z FLEX": "Z-FLEX",
    "Z NYLON": "Z-NYLON",
    "Z ULTRAT": "Z-ULTRAT",
    "BASF BVOH": "BASF ULTRAFUSE BVOH",
    "ULTRAFUSE BVOH": "BASF ULTRAFUSE BVOH",
    "BVOH": "BASF ULTRAFUSE BVOH",
    "EXTERNAL ABS": "ABS-BASED FILAMENT",
    "EXTERNAL PLA": "PLA-BASED FILAMENT",
    "EXTERNAL PETG": "PETG-BASED FILAMENT",
}

# ---------------------------------------------------------------------------
# Metadata parsing / header patching
# ---------------------------------------------------------------------------

@dataclass
class GCodeMetadata:
    model_code: int = 0
    support_code: int = 0
    layer: int | None = None
    quality: int | None = None
    infill: int | None = None
    support_angle: int | None = None
    print_time: int | None = None
    model_length_mm: int | None = None
    support_length_mm: int | None = None
    support_enabled: bool | None = None
    support_type: str | None = None
    top_layers: int | None = None
    bottom_layers: int | None = None
    process: str | None = None
    process_raw: str | None = None
    printer_profile: str | None = None
    printer_profile_raw: str | None = None
    curr_bed_type: str | None = None
    bed_temp_initial: int | None = None
    bed_temp_other: int | None = None
    bed_temp_source: str | None = None
    single_material: bool | None = None
    travel_speed_mm_s: int | None = None
    travel_feedrate: int | None = None
    # Orca extruder speeds are stored in mm/s. Z-code feedrate F is mm/min.
    # Keys are physical tool indexes: 0 = T0/model, 1 = T1/support.
    retraction_speed_mm_s: dict[int, Decimal] = field(default_factory=dict)
    deretraction_speed_mm_s: dict[int, Decimal] = field(default_factory=dict)
    orca_metadata: dict[str, str] = field(default_factory=dict)
    zsuite_hints: dict[str, str] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)

    def mark(self, source: str) -> None:
        if source not in self.sources:
            self.sources.append(source)

    def to_dict(self) -> dict[str, Any]:
        def clean(obj: Any) -> Any:
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {str(k): clean(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [clean(v) for v in obj]
            return obj
        return clean(asdict(self))


def normalize_material_name(name: str) -> str:
    s = name.strip().upper()
    s = s.replace("_", " ")
    s = s.replace("%20", " ")
    s = s.replace(";", " ")
    s = re.sub(r"\s+", " ", s)
    return s


PROFILE_SUFFIX_POLICY = "CANONICAL_PREFIX_PLUS_USER_SUFFIX_ALLOWED"
CANONICAL_ORCA_PROCESS_NAMES = [
    "0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle - single",
    "0.15mm Quality @Zortrax Inventure 0.4 nozzle - single",
    "0.20mm Standard @Zortrax Inventure 0.4 nozzle - single",
    "0.30mm Draft @Zortrax Inventure 0.4 nozzle - single",
    "0.08mm Ultra Quality @Zortrax Inventure 0.4 nozzle - dual",
    "0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual",
    "0.20mm Standard @Zortrax Inventure 0.4 nozzle - dual",
    "0.30mm Draft @Zortrax Inventure 0.4 nozzle - dual",
]
CANONICAL_ORCA_PRINTER_NAMES = [
    "Zortrax Inventure 0.4 nozzle - single",
    "Zortrax Inventure 0.4 nozzle - dual",
]

def _profile_norm(name: str) -> str:
    """Normalize display preset names for tolerant canonical-prefix matching."""
    s = str(name or "").strip().upper()
    s = s.replace("%20", " ").replace("_", " ").replace(";", " ")
    s = re.sub(r"[\[\]\(\){}]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def canonical_profile_prefix(name: str, canonical_names: list[str]) -> str | None:
    """Return canonical preset name if `name` is canonical or canonical + user suffix.

    Examples accepted:
      - `Z-PLA test` -> `Z-PLA` through material map
      - `0.15mm Quality @Zortrax Inventure 0.4 nozzle - dual test`
      - `Zortrax Inventure 0.4 nozzle - single copy`

    The rule is intentionally one-way: the visible Orca preset may append text
    after a known canonical name, but the canonical name itself must remain a
    prefix so unrelated presets are not accidentally matched.
    """
    key = _profile_norm(name)
    if not key:
        return None
    for canon in sorted(canonical_names, key=lambda x: len(_profile_norm(x)), reverse=True):
        c = _profile_norm(canon)
        if key == c or key.startswith(c + " "):
            return canon
    return None

def canonicalize_process_profile(name: str | None) -> str | None:
    return canonical_profile_prefix(name or "", CANONICAL_ORCA_PROCESS_NAMES) or name

def canonicalize_printer_profile(name: str | None) -> str | None:
    return canonical_profile_prefix(name or "", CANONICAL_ORCA_PRINTER_NAMES) or name


def material_code_from_name(name: str) -> int:
    if not name:
        return 0
    key = normalize_material_name(name)
    if key in MATERIAL_CODE_MAP:
        return MATERIAL_CODE_MAP[key]
    alias = MATERIAL_ALIASES.get(key)
    if alias:
        return MATERIAL_CODE_MAP.get(alias, 0)
    # User presets are often renamed with suffixes, e.g. "Z-PLA test".
    # Use longest known canonical/alias prefix as a safe fallback.
    # Same suffix policy is used for process/printer names: canonical name + user suffix is allowed.
    known = sorted(set(MATERIAL_CODE_MAP) | set(MATERIAL_ALIASES), key=len, reverse=True)
    for cand in known:
        c = normalize_material_name(cand)
        if key.startswith(c + " "):
            alias2 = MATERIAL_ALIASES.get(c, c)
            return MATERIAL_CODE_MAP.get(alias2, 0)
    return 0


def infer_fw_triplet(meta: GCodeMetadata) -> tuple[int, int, int]:
    support_enabled = bool(meta.support_enabled)
    support_code = meta.support_code or 0
    if support_enabled and support_code in {0x07, 0x0D, 0x11, 0x13}:
        return (0x01, 0x03, 0x00)
    return (0x01, 0x02, 0x01)


def parse_time_to_seconds(raw: str) -> int | None:
    raw = raw.strip().lower()
    total = 0
    found = False
    for num, unit in re.findall(r"(\d+)\s*([hms])", raw):
        found = True
        n = int(num)
        total += n * (3600 if unit == "h" else 60 if unit == "m" else 1)
    return total if found else None


def parse_orca_metadata(lines: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    in_block = False
    for raw in lines:
        s = raw.strip()
        if s == "; ===== ORCA METADATA BEGIN =====":
            in_block = True
            continue
        if s == "; ===== ORCA METADATA END =====":
            break
        if not in_block or not s.startswith(";"):
            continue
        body = s[1:].strip()
        if "=" not in body:
            continue
        k, v = body.split("=", 1)
        meta[k.strip()] = v.strip().strip('"')
    return meta


def parse_zsuite_hints(lines: list[str]) -> dict[str, str]:
    """Parse optional ZORTRAX ZSUITE HINTS comments.

    The block is a log/semantic bridge from Z-Suite classic setting names to our
    converter.  Values are comments only in Orca, so parsing them must never make
    Orca fail.  This function also accepts any standalone `; zsuite_*=...` line
    so users can keep hints either in a dedicated block or next to ORCA METADATA.
    """
    hints: dict[str, str] = {}
    in_block = False
    for raw in lines:
        s = raw.strip()
        up = s.upper()
        if up == "; ===== ZORTRAX ZSUITE HINTS BEGIN =====":
            in_block = True
            continue
        if up == "; ===== ZORTRAX ZSUITE HINTS END =====":
            in_block = False
            continue
        if not s.startswith(";"):
            continue
        body = s[1:].strip()
        if "=" not in body:
            continue
        k, v = body.split("=", 1)
        key = k.strip()
        if not in_block and not key.lower().startswith("zsuite_"):
            continue
        hints[key.lower()] = v.strip().strip('"')
    return hints



def _parse_keyvals_preserving_quotes(s: str) -> dict[str, str]:
    """Parse key=value pairs in a ZORTRAX diagnostic comment."""
    out: dict[str, str] = {}
    for m in re.finditer(r'([A-Za-z0-9_]+)=("[^"]*"|[^\s]+)', s):
        val = m.group(2).strip()
        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
            val = val[1:-1]
        out[m.group(1).lower()] = val
    return out


def _parse_zcode_value(raw: str | None) -> int:
    if raw is None:
        return 0
    s = str(raw).strip()
    if not s:
        return 0
    try:
        return int(s, 0)
    except ValueError:
        m = re.search(r'0x[0-9a-fA-F]+|\d+', s)
        return int(m.group(0), 0) if m else 0


def parse_zortrax_filament_profiles(lines: list[str]) -> list[dict[str, str]]:
    """Read ;ZORTRAX_FILAMENT_PROFILE comments emitted by Orca filament presets.

    These comments are advisory and are especially important when the visible Orca
    preset name has a user suffix such as "test".  The canonical/zcode pair is
    then safer than guessing from the display name.
    """
    profiles: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in lines:
        s = raw.strip()
        if not s.startswith(';ZORTRAX_FILAMENT_PROFILE'):
            continue
        prof = _parse_keyvals_preserving_quotes(s)
        if not prof:
            continue
        key = (prof.get('canonical',''), prof.get('zcode',''), prof.get('support_role',''))
        if key in seen:
            continue
        seen.add(key)
        profiles.append(prof)
    return profiles


def _profile_name_matches(material_name: str, profile_value: str | None) -> bool:
    if not material_name or not profile_value:
        return False
    wanted = normalize_material_name(material_name)
    cand = normalize_material_name(profile_value)
    if not wanted or not cand:
        return False
    return wanted == cand or wanted.startswith(cand + ' ') or cand.startswith(wanted + ' ')


def _profile_code_for_material(profiles: list[dict[str, str]], material_name: str, support_role: int | None = None) -> int:
    if not material_name:
        return 0
    # Prefer profiles with the expected model/support role.
    candidates = profiles
    if support_role is not None:
        role_filtered = [p for p in profiles if str(p.get('support_role','')).strip() == str(int(support_role))]
        if role_filtered:
            candidates = role_filtered
    for prof in candidates:
        for field in ('name', 'canonical'):
            if _profile_name_matches(material_name, prof.get(field)):
                code = _parse_zcode_value(prof.get('zcode'))
                if code:
                    return code
    # Last fallback: exact map via profile canonical/name if the material name itself maps to zero.
    return 0


def _apply_filament_profile_material_codes(meta: GCodeMetadata, profiles: list[dict[str, str]]) -> None:
    """Use ZORTRAX_FILAMENT_PROFILE canonical/zcode comments as material-code fallback.

    Policy: Orca preset names may be renamed by the user (e.g. "Z-PLA test").
    The profile comment stores the canonical material and code, so it should be
    used when ordinary name mapping fails.  It does not change temperatures or
    movement profiles; those still come from Orca metadata/markers and converter
    logic.
    """
    if not profiles:
        return
    t0_name = meta.orca_metadata.get('filament_t0') or meta.orca_metadata.get('filament_type_t0') or ''
    t1_name = meta.orca_metadata.get('filament_t1') or meta.orca_metadata.get('filament_type_t1') or meta.orca_metadata.get('support_material') or ''
    if not meta.model_code:
        code = _profile_code_for_material(profiles, t0_name, support_role=0)
        if code:
            meta.model_code = code
            meta.mark('ZORTRAX_FILAMENT_PROFILE:model')
    if not meta.support_code:
        code = _profile_code_for_material(profiles, t1_name, support_role=1)
        if code:
            meta.support_code = code
            meta.mark('ZORTRAX_FILAMENT_PROFILE:support')

def parse_mm_pair(raw: str) -> tuple[int | None, int | None]:
    vals = [v.strip() for v in raw.split(",")]
    nums: list[int | None] = []
    for v in vals[:2]:
        try:
            nums.append(int(round(float(v))))
        except ValueError:
            nums.append(None)
    while len(nums) < 2:
        nums.append(None)
    return nums[0], nums[1]


def first_int(text: str) -> int | None:
    m = re.search(r"-?\d+", text)
    return int(m.group(0)) if m else None


def first_decimal(text: str) -> Decimal | None:
    m = re.search(r"[-+]?\d*\.?\d+", str(text))
    if not m:
        return None
    try:
        return Decimal(m.group(0))
    except Exception:
        return None


def _orca_value_for_tool(orca: dict[str, str], base: str, tool: int) -> str | None:
    candidates = (f"{base}_t{tool}", f"{base}_T{tool}", f"{base}_{tool}", f"{base}[{tool}]")
    for k in candidates:
        if k in orca and str(orca[k]).strip() != "":
            return orca[k]
    # Orca full comments often store vector values as: base = v0,v1.
    if base in orca and str(orca[base]).strip() != "":
        vals = [v.strip().strip('"\'') for v in str(orca[base]).split(',')]
        if 0 <= int(tool) < len(vals) and vals[int(tool)] != "":
            return vals[int(tool)]
    return None


def parse_bool(text: str) -> bool | None:
    s = text.strip().lower()
    if s in {"true", "1", "yes", "on"}:
        return True
    if s in {"false", "0", "no", "off"}:
        return False
    return None


def infer_quality(layer_hundredths: int | None, existing: int | None = None) -> int | None:
    if layer_hundredths is None:
        return existing
    if layer_hundredths in (15, 20):
        return 1
    if layer_hundredths == 30:
        return 2
    if layer_hundredths == 8:
        return 1
    return existing if existing is not None else 1


def looks_like_support_material(name: str) -> bool:
    return "SUPPORT" in normalize_material_name(name) or "BVOH" in normalize_material_name(name)


def _apply_filename_fallback(meta: GCodeMetadata, gcode_path: Path) -> None:
    parts = gcode_path.stem.split("_")
    if len(parts) < 4:
        return

    print_time = parse_time_to_seconds(parts[-1])
    if print_time:
        meta.print_time = print_time
        meta.mark("filename:print_time")

    model_from_name = material_code_from_name(parts[-3])
    if model_from_name:
        meta.model_code = model_from_name
        meta.mark("filename:model")

    support_from_name = material_code_from_name(parts[-2])
    if support_from_name:
        meta.support_code = support_from_name
        meta.mark("filename:support")


def _norm_bed_type_name(text: str | None) -> str:
    return (text or "").strip().lower().replace("-", " ").replace("_", " ")

def _plate_prefix_from_curr_bed_type(curr_bed_type: str | None) -> str | None:
    s = _norm_bed_type_name(curr_bed_type)
    mapping = {
        "smooth cool plate": "cool",
        "cool plate": "cool",
        "smooth high temp plate": "hot",
        "high temp plate": "hot",
        "textured cool plate": "textured_cool",
        "textured pei plate": "textured",
        "textured plate": "textured",
        "engineering plate": "eng",
        "eng plate": "eng",
        "cool plate (supertack)": "supertack",
        "supertack": "supertack",
        "supertack plate": "supertack",
    }
    if s in mapping:
        return mapping[s]
    if "supertack" in s:
        return "supertack"
    if "textured" in s and "cool" in s:
        return "textured_cool"
    if "textured" in s:
        return "textured"
    if "engineering" in s or s == "eng":
        return "eng"
    if "high" in s or "hot" in s:
        return "hot"
    if "cool" in s:
        return "cool"
    return None

def _first_int_from_meta(orca: dict[str, str], keys: list[str]) -> tuple[int | None, str | None]:
    for key in keys:
        if key in orca and str(orca[key]).strip() != "":
            value = first_int(str(orca[key]))
            if value is not None:
                return value, key
    return None, None

def _apply_bed_temperature_metadata(meta: GCodeMetadata, orca: dict[str, str]) -> None:
    curr = orca.get("curr_bed_type")
    if curr:
        meta.curr_bed_type = curr
        meta.mark("ORCA_METADATA:curr_bed_type")
    prefix = _plate_prefix_from_curr_bed_type(curr)

    prefix_to_keys = {
        "supertack": ("bed_temp_supertack_initial", "bed_temp_supertack"),
        "cool": ("bed_temp_cool_initial", "bed_temp_cool"),
        "textured_cool": ("bed_temp_textured_cool_initial", "bed_temp_textured_cool"),
        "eng": ("bed_temp_eng_initial", "bed_temp_eng"),
        "hot": ("bed_temp_hot_initial", "bed_temp_hot"),
        "textured": ("bed_temp_textured_initial", "bed_temp_textured"),
    }

    initial_keys: list[str] = []
    other_keys: list[str] = []
    if prefix and prefix in prefix_to_keys:
        ik, ok = prefix_to_keys[prefix]
        initial_keys.append(ik)
        other_keys.append(ok)

    # Fallback order if curr_bed_type is absent or not recognized.
    for p in ("hot", "eng", "textured", "textured_cool", "cool", "supertack"):
        ik, ok = prefix_to_keys[p]
        if ik not in initial_keys:
            initial_keys.append(ik)
        if ok not in other_keys:
            other_keys.append(ok)

    initial, initial_key = _first_int_from_meta(orca, initial_keys)
    other, other_key = _first_int_from_meta(orca, other_keys)

    if initial is not None:
        meta.bed_temp_initial = initial
        meta.bed_temp_source = initial_key
        meta.mark(f"ORCA_METADATA:bed_temp_initial:{initial_key}")
    if other is not None:
        meta.bed_temp_other = other
        meta.mark(f"ORCA_METADATA:bed_temp_other:{other_key}")


def _apply_orca_block(meta: GCodeMetadata) -> None:
    if not meta.orca_metadata:
        return
    orca = meta.orca_metadata
    meta.mark("ORCA_METADATA")
    raw_process = orca.get("process")
    meta.process_raw = raw_process
    meta.process = canonicalize_process_profile(raw_process)
    if raw_process and meta.process != raw_process:
        meta.mark("ORCA_METADATA:process_suffix_canonicalized")

    raw_printer = orca.get("printer") or orca.get("printer_preset") or orca.get("printer_settings_id")
    meta.printer_profile_raw = raw_printer
    meta.printer_profile = canonicalize_printer_profile(raw_printer)
    if raw_printer and meta.printer_profile != raw_printer:
        meta.mark("ORCA_METADATA:printer_suffix_canonicalized")

    # v1.16: Orca bed temperatures are plate-type dependent.
    # curr_bed_type selects the active plate, then the matching *_plate_temp* metadata is used.
    _apply_bed_temperature_metadata(meta, orca)

    t0_name = orca.get("filament_t0") or orca.get("filament_type_t0")
    if t0_name:
        code = material_code_from_name(t0_name)
        if code:
            meta.model_code = code
            meta.mark("ORCA_METADATA:model")

    t1_name = orca.get("filament_t1") or orca.get("filament_type_t1")
    if t1_name:
        code = material_code_from_name(t1_name)
        if code:
            meta.support_code = code
            meta.mark("ORCA_METADATA:support")

    if orca.get("layer_height"):
        try:
            meta.layer = int(round(float(orca["layer_height"]) * 100))
            meta.mark("ORCA_METADATA:layer")
        except ValueError:
            pass

    if orca.get("support_threshold_angle"):
        value = first_int(orca["support_threshold_angle"])
        if value is not None:
            meta.support_angle = value
            meta.mark("ORCA_METADATA:support_angle")

    if orca.get("infill_density"):
        value = first_int(orca["infill_density"])
        if value is not None:
            meta.infill = value
            meta.mark("ORCA_METADATA:infill")

    if orca.get("top_layers"):
        meta.top_layers = first_int(orca["top_layers"])
        meta.mark("ORCA_METADATA:top_layers")

    if orca.get("bottom_layers"):
        meta.bottom_layers = first_int(orca["bottom_layers"])
        meta.mark("ORCA_METADATA:bottom_layers")

    if orca.get("support") is not None:
        meta.support_enabled = parse_bool(orca["support"])
        meta.mark("ORCA_METADATA:support_enabled")

    if orca.get("support_type") is not None:
        meta.support_type = orca["support_type"]
        meta.mark("ORCA_METADATA:support_type")

    if orca.get("travel_speed") is not None:
        value = first_int(orca["travel_speed"])
        if value is not None:
            meta.travel_speed_mm_s = value
            meta.travel_feedrate = int(value) * 60
            meta.mark("ORCA_METADATA:travel_speed")

    # v1.06: per-tool Orca extruder speeds. Orca placeholders are mm/s;
    # the converter multiplies by 60 when emitting Z-code feedrate commands.
    for tool in (0, 1):
        rv = _orca_value_for_tool(orca, "retraction_speed", tool)
        if rv is not None:
            val = first_decimal(rv)
            if val is not None:
                meta.retraction_speed_mm_s[tool] = val
                meta.mark(f"ORCA_METADATA:retraction_speed_t{tool}")
        dv = _orca_value_for_tool(orca, "deretraction_speed", tool)
        if dv is not None:
            val = first_decimal(dv)
            if val is not None:
                meta.deretraction_speed_mm_s[tool] = val
                meta.mark(f"ORCA_METADATA:deretraction_speed_t{tool}")


def _apply_comment_fallbacks(meta: GCodeMetadata, lines: list[str]) -> None:
    for line in lines:
        s = line.strip()
        # Preserve selected full Orca footer settings as metadata fallbacks.
        # These are not always present inside the custom ORCA METADATA block.
        if s.startswith(";") and "=" in s:
            body = s[1:].strip()
            k, v = body.split("=", 1)
            key = k.strip()
            val = v.strip().strip('"')
            if key in {
                "nozzle_temperature", "nozzle_temperature_initial_layer",
                "idle_temperature", "standby_temperature_delta",
                "ooze_prevention", "preheat_time",
                "nozzle_temperature_range_low", "nozzle_temperature_range_high",
            }:
                meta.orca_metadata.setdefault(key, val)
                meta.mark(f"comment:{key}")
        if s.startswith("; estimated printing time"):
            secs = parse_time_to_seconds(s.split("=", 1)[1].strip())
            if secs:
                meta.print_time = secs
                meta.mark("comment:print_time")
        elif s.startswith("; filament used [mm] = "):
            m0, m1 = parse_mm_pair(s.split("=", 1)[1].strip())
            if m0 is not None:
                meta.model_length_mm = m0
                meta.mark("comment:model_mm")
            if m1 is not None:
                meta.support_length_mm = m1
                meta.mark("comment:support_mm")
        elif s.startswith("; filament_type = ") and meta.model_code == 0:
            vals = [x.strip().strip('"') for x in s.split("=", 1)[1].split(",")]
            if vals:
                code = material_code_from_name(vals[0])
                if code:
                    meta.model_code = code
                    meta.mark("comment:model")
            if len(vals) > 1 and meta.support_code == 0:
                code = material_code_from_name(vals[1])
                if code:
                    meta.support_code = code
                    meta.mark("comment:support")
        elif s.startswith("; filament_settings_id = "):
            vals = [x.strip().strip('"') for x in s.split("=", 1)[1].split(",")]
            if vals and meta.model_code == 0:
                code = material_code_from_name(vals[0])
                if code:
                    meta.model_code = code
                    meta.mark("comment:model_settings_id")
            if len(vals) > 1 and meta.support_code == 0:
                code = material_code_from_name(vals[1])
                if code:
                    meta.support_code = code
                    meta.mark("comment:support_settings_id")
        elif s.startswith("; layer_height = ") and meta.layer is None:
            try:
                meta.layer = int(round(float(s.split("=", 1)[1].strip()) * 100))
                meta.mark("comment:layer")
            except ValueError:
                pass
        elif s.startswith("; sparse_infill_density = ") and meta.infill is None:
            value = first_int(s)
            if value is not None:
                meta.infill = value
                meta.mark("comment:infill")
        elif s.startswith("; support_threshold_angle = ") and meta.support_angle is None:
            value = first_int(s)
            if value is not None:
                meta.support_angle = value
                meta.mark("comment:support_angle")
        elif s.startswith("; travel_speed = ") and meta.travel_feedrate is None:
            value = first_int(s)
            if value is not None:
                meta.travel_speed_mm_s = value
                meta.travel_feedrate = int(value) * 60
                meta.mark("comment:travel_speed")
        elif s.startswith("; retraction_speed = "):
            vals = [v.strip() for v in s.split("=", 1)[1].split(",")]
            for i, raw in enumerate(vals[:2]):
                val = first_decimal(raw)
                if val is not None:
                    meta.retraction_speed_mm_s[i] = val
                    meta.mark(f"comment:retraction_speed_t{i}")
        elif s.startswith("; deretraction_speed = "):
            vals = [v.strip() for v in s.split("=", 1)[1].split(",")]
            for i, raw in enumerate(vals[:2]):
                val = first_decimal(raw)
                if val is not None:
                    meta.deretraction_speed_mm_s[i] = val
                    meta.mark(f"comment:deretraction_speed_t{i}")


def _apply_single_material_rules(meta: GCodeMetadata) -> None:
    meta.quality = infer_quality(meta.layer, meta.quality)

    support_len = meta.support_length_mm
    support_code = meta.support_code or 0
    model_code = meta.model_code or 0

    if support_len == 0 or (support_len is None and (support_code == 0 or support_code == model_code)):
        meta.single_material = True
        if model_code and not support_code:
            meta.support_code = model_code
            meta.mark("derived:single_material_support_equals_model")
        if meta.support_length_mm is None:
            meta.support_length_mm = 0
            meta.mark("derived:single_material_support_mm_zero")
    else:
        meta.single_material = False

    t1_name = str(meta.orca_metadata.get("filament_t1", ""))
    if model_code and meta.support_length_mm == 0 and meta.support_code and not looks_like_support_material(t1_name):
        meta.support_code = model_code
        meta.single_material = True
        meta.mark("derived:single_material_override_support_code")

    if meta.support_enabled is None:
        meta.support_enabled = (meta.support_length_mm or 0) > 0


def parse_metadata_from_gcode(gcode_path: Path) -> GCodeMetadata:
    text = gcode_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    meta = GCodeMetadata(orca_metadata=parse_orca_metadata(lines), zsuite_hints=parse_zsuite_hints(lines))
    if getattr(meta, "zsuite_hints", None):
        meta.mark("ZSUITE_HINTS")
    _apply_filename_fallback(meta, gcode_path)
    _apply_orca_block(meta)
    _apply_comment_fallbacks(meta, lines)
    _apply_filament_profile_material_codes(meta, parse_zortrax_filament_profiles(lines))
    _apply_single_material_rules(meta)
    return meta


def parse_software_version(raw: str) -> tuple[int, int, int, int]:
    parts = tuple(int(x) for x in raw.split("."))
    if len(parts) != 4:
        raise SystemExit("software version must have 4 parts, e.g. 2.32.0.0")
    return parts  # type: ignore[return-value]


def write_int_le(buf: bytearray, offset: int, length: int, value: int) -> None:
    for i in range(length):
        buf[offset + i] = (value >> (8 * i)) & 0xFF


def crc8_d5(data: bytes) -> int:
    poly = 0xD5
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc & 0xFF


def patch_classic_zcode(
    zcode_path: Path,
    meta: GCodeMetadata,
    software: tuple[int, int, int, int] = (2, 32, 0, 0),
    device_id: int = DEVICE_IDS["INVENTURE"],
) -> None:
    buf = bytearray(zcode_path.read_bytes())
    if len(buf) < HEADER_MIN_LEN or buf[: len(HEADER_MAGIC)] != HEADER_MAGIC:
        raise ValueError("Not a classic ZCode file")

    fw_a, fw_b, fw_c = infer_fw_triplet(meta)
    buf[OFFSET_FW_TRIPLET] = fw_a & 0xFF
    buf[OFFSET_FW_TRIPLET + 1] = fw_b & 0xFF
    buf[OFFSET_FW_TRIPLET + 2] = fw_c & 0xFF
    buf[OFFSET_DEVICE_ID] = device_id & 0xFF

    if meta.model_code:
        buf[OFFSET_MODEL_MATERIAL] = meta.model_code & 0xFF
    if meta.layer is not None:
        buf[OFFSET_LAYER] = meta.layer & 0xFF
    if meta.quality is not None:
        buf[OFFSET_QUALITY] = meta.quality & 0xFF
    if meta.infill is not None:
        buf[OFFSET_INFILL] = meta.infill & 0xFF
    if meta.support_angle is not None:
        buf[OFFSET_SUPPORT_ANGLE] = meta.support_angle & 0xFF
    if meta.print_time is not None:
        write_int_le(buf, OFFSET_PRINT_TIME, 4, int(meta.print_time))

    # Project findings treat 73..74 and 77..78 as the confirmed filament-length fields.
    if meta.model_length_mm is not None:
        write_int_le(buf, OFFSET_MODEL_LENGTH_MM, 2, int(meta.model_length_mm))
    if meta.support_length_mm is not None:
        write_int_le(buf, OFFSET_SUPPORT_LENGTH_MM, 2, int(meta.support_length_mm))

    a, b, c, d = software
    buf[OFFSET_SOFTWARE_VERSION] = a & 0xFF
    buf[OFFSET_SOFTWARE_VERSION + 1] = b & 0xFF
    buf[OFFSET_SOFTWARE_VERSION + 2] = c & 0xFF
    buf[OFFSET_SOFTWARE_VERSION + 3] = d & 0xFF

    if meta.support_code:
        buf[OFFSET_SUPPORT_MATERIAL] = meta.support_code & 0xFF
    elif meta.model_code:
        buf[OFFSET_SUPPORT_MATERIAL] = meta.model_code & 0xFF

    buf[OFFSET_HEADER_CRC] = crc8_d5(bytes(buf[:OFFSET_HEADER_CRC]))
    zcode_path.write_bytes(bytes(buf))


def build_report(meta: GCodeMetadata, header_crc: int | None = None) -> str:
    triplet = infer_fw_triplet(meta)
    parts = [
        f"model=0x{meta.model_code:02X}",
        f"support=0x{meta.support_code:02X}",
        f"layer={meta.layer}",
        f"quality={meta.quality}",
        f"infill={meta.infill}",
        f"support_angle={meta.support_angle}",
        f"print_time={meta.print_time}",
        f"model_mm={meta.model_length_mm}",
        f"support_mm={meta.support_length_mm}",
        f"single_material={meta.single_material}",
        f"travel_speed_mm_s={meta.travel_speed_mm_s}",
        f"retraction_speed_mm_s={dict(meta.retraction_speed_mm_s)}",
        f"deretraction_speed_mm_s={dict(meta.deretraction_speed_mm_s)}",
        f"travel_feedrate={meta.travel_feedrate}",
        f"fw_triplet={triplet[0]:02X}-{triplet[1]:02X}-{triplet[2]:02X}",
    ]
    if header_crc is not None:
        parts.append(f"header_crc=0x{header_crc:02X}")
    if meta.sources:
        parts.append(f"sources={';'.join(meta.sources)}")
    return ", ".join(parts)

# ---------------------------------------------------------------------------
# Console-safe output / progress reporting
# ---------------------------------------------------------------------------

def _stream_encoding(stream: Any) -> str:
    return getattr(stream, 'encoding', None) or 'utf-8'


def _console_text(text: object, stream: Any = None) -> str:
    s = str(text)
    enc = _stream_encoding(stream or sys.stdout)
    try:
        s.encode(enc)
        return s
    except Exception:
        fallback = s.translate({ord('↳'): '->', ord('≈'): '~', ord('—'): '-'})
        try:
            fallback.encode(enc)
            return fallback
        except Exception:
            return fallback.encode(enc, errors='replace').decode(enc, errors='replace')


def console_print(*args: object, sep: str = ' ', end: str = "\n", flush: bool = True, stream: Any = None, log: bool = True) -> None:
    stream = stream or sys.stdout
    text = sep.join(str(a) for a in args)
    rendered = _console_text(text, stream)
    print(rendered, end=end, flush=flush, file=stream)
    if log and end.endswith('\n'):
        _append_log_line(text)


def diagnostic_print(*args: object, sep: str = ' ') -> None:
    """Log repetitive conversion diagnostics without breaking the progress bar.

    Set environment variable G2Z_VERBOSE=1/true/yes to also mirror these
    diagnostics to the console. By default they go only to orca_postprocess_last.log.
    """
    text = sep.join(str(a) for a in args)
    _append_log_line(text)
    if (os.environ.get('G2Z_VERBOSE') or '').strip().lower() in {'1', 'true', 'yes', 'on'}:
        console_print(text, log=False)


def _enable_windows_vt(stream: Any) -> bool:
    if os.name != 'nt':
        return False
    if not hasattr(stream, 'isatty') or not stream.isatty():
        return False
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-12 if stream is sys.stderr else -11)
        if handle in (0, -1):
            return False
        mode = wintypes.DWORD()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return False
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        if kernel32.SetConsoleMode(handle, new_mode) == 0:
            return False
        return True
    except Exception:
        return False


def _supports_dashboard(stream: Any) -> bool:
    if not hasattr(stream, 'isatty') or not stream.isatty():
        return False
    if os.name == 'nt':
        return _enable_windows_vt(stream) or bool(
            os.environ.get('WT_SESSION')
            or os.environ.get('ANSICON')
            or os.environ.get('ConEmuANSI') == 'ON'
            or os.environ.get('TERM_PROGRAM') == 'vscode'
        )
    term = (os.environ.get('TERM') or '').lower()
    return term != 'dumb'


class ProgressReporter:
    def __init__(self, enabled: bool = True, width: int = 24) -> None:
        self.enabled = enabled
        self.width = width
        self._last_stage: str | None = None
        self._last_percent = -1
        self._progress_active = False
        style = (os.environ.get('G2Z_PROGRESS_STYLE') or 'plain').strip().lower()
        use_dashboard = style in {'dashboard', 'two-line', 'twoline'} and _supports_dashboard(sys.stderr)
        self._status_stream = sys.stderr if use_dashboard else sys.stdout
        self._use_dashboard = use_dashboard
        self._dashboard_active = False

    def _stage_line(self, stage: str, detail: str | None) -> str:
        summary = ''
        if detail:
            summary = ' | '.join(part.strip() for part in str(detail).splitlines() if part.strip())
        if summary:
            return _console_text(f'Current step: {stage} | {summary}', self._status_stream)
        return _console_text(f'Current step: {stage}', self._status_stream)

    def _progress_line(self, percent: int) -> str:
        filled = int(round(self.width * percent / 100))
        bar = '#' * filled + '-' * (self.width - filled)
        return _console_text(f'Progress: [{bar}] {percent:3d}%', self._status_stream)

    def _render_dashboard(self, percent: int, stage: str, detail: str | None) -> None:
        stage_line = self._stage_line(stage, detail)
        progress_line = self._progress_line(percent)
        if self._dashboard_active:
            self._status_stream.write('\x1b[2F')
            self._status_stream.write('\x1b[2K' + stage_line + '\n')
            self._status_stream.write('\x1b[2K' + progress_line)
        else:
            self._status_stream.write(stage_line + '\n' + progress_line)
            self._dashboard_active = True
        self._status_stream.flush()

    def _render_plain(self, percent: int, stage: str, detail: str | None) -> None:
        stage_changed = (stage != self._last_stage) or (detail is not None and stage == self._last_stage and percent == self._last_percent == -1)
        stage_text = self._stage_line(stage, detail)
        progress_text = self._progress_line(percent)

        if stage_changed:
            if self._progress_active:
                self._status_stream.write('\n')
            self._status_stream.write(stage_text + '\n')
            self._status_stream.write(progress_text)
            self._status_stream.flush()
            self._progress_active = True
            _append_log_line(stage_text)
            _append_log_line(progress_text)
        else:
            self._status_stream.write('\r' + progress_text)
            self._status_stream.flush()
            _append_log_line(progress_text)

    def update(self, percent: int, stage: str, detail: str | None = None, *, force: bool = False) -> None:
        if not self.enabled:
            return
        percent = max(0, min(100, int(percent)))
        if not force and percent == self._last_percent and stage == self._last_stage and detail is None:
            return
        if self._use_dashboard:
            self._render_dashboard(percent, stage, detail)
        else:
            self._render_plain(percent, stage, detail)
        self._last_percent = percent
        self._last_stage = stage

    def break_line(self) -> None:
        if self._use_dashboard:
            return
        if self._progress_active:
            self._status_stream.write('\n')
            self._status_stream.flush()
            self._progress_active = False

    def finish(self, stage: str = 'Finished', detail: str | None = None) -> None:
        self.update(100, stage, detail, force=True)
        if self._use_dashboard and self._dashboard_active:
            self._status_stream.write('\n')
            self._status_stream.flush()
            self._dashboard_active = False
        elif self._progress_active:
            self._status_stream.write('\n')
            self._status_stream.flush()
            self._progress_active = False

def _scaled_percent(index: int, total: int, start_pct: int, end_pct: int) -> int:
    if total <= 0:
        return end_pct
    span = max(0, end_pct - start_pct)
    return start_pct + int(span * index / total)


# ---------------------------------------------------------------------------
# Zortrax Inventure special cleaning markers
# ---------------------------------------------------------------------------

SPECIAL_POSITION_CODES = {
    "GARBAGECENTER": 0x00, "GARBAGE_CENTER": 0x00,
    "EXTRUDERSWITCHINGTOMODELSLOW": 0x01, "MODEL_SLOW": 0x01, "T0_SLOW": 0x01,
    "EXTRUDERSWITCHINGTOSUPPORTSLOW": 0x02, "SUPPORT_SLOW": 0x02, "T1_SLOW": 0x02,
    "EXTRUDERSWITCHINGTOMODELFAST": 0x03, "MODEL_FAST": 0x03, "T0_FAST": 0x03,
    "EXTRUDERSWITCHINGTOSUPPORTFAST": 0x04, "SUPPORT_FAST": 0x04, "T1_FAST": 0x04,
    "EXTRUDERSWITCHINGTOMODELBRUSHAVOID": 0x05, "MODEL_BRUSH_AVOID": 0x05, "T0_BRUSH_AVOID": 0x05,
    "EXTRUDERSWITCHINGTOSUPPORTBRUSHAVOID": 0x06, "SUPPORT_BRUSH_AVOID": 0x06, "T1_BRUSH_AVOID": 0x06,
    "EXTRUDERSWITCHINGTOMODELGARBAGESIDE": 0x07, "MODEL_GARBAGE_SIDE": 0x07, "T0_GARBAGE_SIDE": 0x07,
    "EXTRUDERSWITCHINGTOSUPPORTGARBAGESIDE": 0x08, "SUPPORT_GARBAGE_SIDE": 0x08, "T1_GARBAGE_SIDE": 0x08,
    "EXTRUDERSWITCHINGTOMODELGARBAGEOUTSIDE": 0x09, "MODEL_GARBAGE_OUTSIDE": 0x09, "T0_GARBAGE_OUTSIDE": 0x09,
    "EXTRUDERSWITCHINGTOSUPPORTGARBAGEOUTSIDE": 0x0A, "SUPPORT_GARBAGE_OUTSIDE": 0x0A, "T1_GARBAGE_OUTSIDE": 0x0A,
    "HOTENDCLEANINGPOSITION": 0x0B, "HOTEND_CLEANING_POSITION": 0x0B, "HOTEND_CLEAN": 0x0B,
}

SPECIAL_CLEAN_SEQUENCES = {
    "SINGLE": [0x05, 0x0A, 0x03, 0x01, 0x00],
    "T0": [0x0B, 0x05, 0x09, 0x03, 0x01, 0x00],
    "MODEL": [0x0B, 0x05, 0x09, 0x03, 0x01, 0x00],
    "T1": [0x0B, 0x06, 0x0A, 0x04, 0x02, 0x00],
    "SUPPORT": [0x0B, 0x06, 0x0A, 0x04, 0x02, 0x00],
    "DUAL_FULL": [0x06, 0x09, 0x04, 0x02, 0x00, 0x09, 0x07, 0x0A, 0x08, 0x09, 0x07, 0x00],
}

def _normalize_marker_token(text: str) -> str:
    token = text.strip().upper().replace("-", "_").replace(" ", "_")
    return re.sub(r"[^A-Z0-9_]+", "", token)

def special_position_code_from_token(token: str) -> int | None:
    raw = token.strip()
    if not raw:
        return None
    try:
        value = int(raw, 16) if raw.lower().startswith("0x") else int(raw)
        if 0 <= value <= 0xFF:
            return value
    except ValueError:
        pass
    return SPECIAL_POSITION_CODES.get(_normalize_marker_token(raw))

def zcmd_special_position(code: int) -> bytes:
    return zcmd_simple(17, code & 0xFF)

def zcmd_special_clean_sequence(mode: str, active_tool: int, single_material: bool | None) -> list[bytes]:
    key = _normalize_marker_token(mode or "AUTO")
    if key in {"AUTO", "CURRENT", "CURRENT_TOOL"}:
        if single_material:
            key = "SINGLE"
        else:
            key = "T1" if active_tool == 1 else "T0"
    elif key in {"DUAL", "FULL_DUAL"}:
        key = "DUAL_FULL"
    elif key in {"0", "TOOL0", "EXTRUDER0"}:
        key = "T0"
    elif key in {"1", "TOOL1", "EXTRUDER1"}:
        key = "T1"
    if key == "SINGLE":
        return list(ZS_CLEAN_MACHINE_SEQUENCES["SINGLE"])
    if key == "DUAL_FULL":
        return list(ZS_CLEAN_MACHINE_SEQUENCES["DUAL"])
    seq = SPECIAL_CLEAN_SEQUENCES.get(key)
    if seq is None:
        raise ValueError(f"Unknown ZORTRAX_SPECIAL_CLEAN mode: {mode!r}")
    return [zcmd_special_position(code) for code in seq]

# ---------------------------------------------------------------------------
# Z-Suite-like machine start/end markers
# ---------------------------------------------------------------------------
#
# These sequences were extracted from reference Inventure .zcode files produced
# by Z-Suite for bunnydecor x1. They intentionally stop before model-specific
# travel/printing moves in the start sequence. The commands are emitted as
# already-CRCed classic ZCode commands, because several of them are still only
# partially understood at the semantic level.
#
# Marker syntax accepted in Orca G-code comments:
#   ;ZORTRAX_START_MACHINE AUTO|SINGLE|DUAL
#   ;ZORTRAX_END_MACHINE AUTO|SINGLE|DUAL
#
# AUTO chooses SINGLE when metadata says single-material; otherwise DUAL.

ZS_START_SINGLE_BASE_HEX = """
03 0b 00 15
07 04 08 00 00 00 00 c2
08 01 ff 10 00 00 00 00 a7
06 0e 1e 00 00 00 cd
06 16 1e 00 00 00 b5
07 08 00 d2 00 00 00 c0
02 14 ba
03 05 03 dd
03 05 04 89
0f 04 07 00 00 00 00 00 00 00 00 00 00 00 00 c3
06 02 b4 00 00 00 fe
08 01 ff 04 fe 2e 00 00 30
06 1c 00 00 00 00 25
03 1a 01 7b
06 10 f8 ff ff ff 36
03 1a 03 04
06 02 20 1c 00 00 46
03 11 05 c0
06 02 20 1c 00 00 46
03 11 0a bd
06 02 20 1c 00 00 46
03 11 03 41
06 02 fa 00 00 00 25
03 11 01 3e
03 07 00 61
06 02 20 1c 00 00 46
03 11 00 eb
"""

ZS_START_DUAL_STATIC_REFERENCE_HEX = """
03 0b 00 15
07 04 08 00 00 00 00 c2
08 01 ff 10 00 00 00 00 a7
06 0e 28 00 00 00 a1
06 16 28 00 00 00 d9
07 08 01 dc 00 00 00 6a
07 08 00 5a 00 00 00 cc
02 14 ba
03 05 03 dd
03 05 04 89
0f 04 07 00 00 00 00 00 00 00 00 00 00 00 00 c3
06 02 b4 00 00 00 fe
08 01 ff 04 fe 2e 00 00 30
06 1c 00 00 00 00 25
03 1a 01 7b
06 10 fa ff ff ff bc
03 1a 03 04
06 02 20 1c 00 00 46
03 11 06 6a
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 04 15
06 02 fa 00 00 00 25
03 11 02 94
03 07 01 b4
06 02 20 1c 00 00 46
03 11 00 eb
06 02 e0 01 00 00 d5
08 01 ea 08 93 52 00 00 b0
06 02 10 0e 00 00 ab
08 01 fe 08 26 5a 00 00 cd
06 0c b8 0b 00 00 5b
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 07 bf
06 02 20 1c 00 00 46
03 11 0a bd
06 02 20 1c 00 00 46
03 11 08 c2
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 07 bf
06 02 20 1c 00 00 46
03 11 00 eb
06 02 10 0e 00 00 ab
08 01 fd 08 a6 52 00 00 0d
07 04 08 00 00 00 00 c2
03 1a 67 c3
03 15 03 6d
06 02 20 1c 00 00 46
"""


# Dynamic Z-Suite-like START_MACHINE profiles.
# Values come from original Z-Suite Inventure references analyzed in the project.
# Exact material/profile matches are preferred; unknown materials fall back to averages
# computed from the currently available references. Lengths are millimetres of filament.
ZSUITE_START_SINGLE_E_PROFILES: dict[tuple[str, ...], tuple[str, tuple[str, str, str]]] = {
    ("Z-ABS",): ("native Z-ABS reference", ("20.000", "20.802", "20.002")),
    ("Z-ULTRAT",): ("native Z-ULTRAT reference", ("20.000", "21.020", "20.020")),
    ("Z-GLASS",): ("native Z-GLASS reference", ("20.000", "22.000", "20.000")),
    ("Z-PETG",): ("native Z-PETG reference", ("20.000", "22.000", "20.000")),
    ("Z-FLEX",): ("single Z-FLEX reference", ("20.000", "22.500", "20.000")),
    ("Z-PLA",): ("single Z-PLA reference", ("20.000", "21.000", "20.000")),
    ("Z-PLA PRO",): ("native Z-PLA Pro reference", ("20.000", "21.504", "20.004")),
    ("Z-ASA PRO",): ("native Z-ASA Pro reference", ("20.000", "21.000", "20.000")),
    ("Z-NYLON",): ("native Z-NYLON reference", ("20.000", "22.000", "20.000")),
    ("PETG-BASED FILAMENT",): ("external PETG-based reference", ("20.000", "22.000", "20.000")),
    ("GLASS-TYPE FILAMENT",): ("external GLASS-type reference", ("20.000", "22.000", "20.000")),
    ("PLA-BASED FILAMENT",): ("external PLA-based reference", ("20.000", "21.000", "20.000")),
    ("FLEX-BASED FILAMENT",): ("external FLEX-based reference", ("20.000", "22.500", "20.000")),
    ("NYLON-BASED FILAMENT",): ("external NYLON-based reference", ("20.000", "22.000", "20.000")),
    ("ULTRAT-BASED FILAMENT",): ("external ULTRAT-based reference", ("20.000", "21.020", "20.020")),
    ("ESD PETG-BASED FILAMENT",): ("external ESD PETG-based reference", ("20.000", "21.804", "20.004")),
    ("PLA PRO-BASED FILAMENT",): ("external PLA Pro-based reference", ("20.000", "21.504", "20.004")),
    ("ASA PRO-BASED FILAMENT",): ("external ASA Pro-based reference", ("20.000", "21.000", "20.000")),
    ("SEMIFLEX-BASED FILAMENT",): ("external SEMIFLEX-based reference", ("22.020", "24.040", "22.040")),
}
ZSUITE_START_SINGLE_E_FALLBACK = (
    "single averaged fallback from references",
    ("20.00", "21.75", "20.00"),
)

# v1.2.9/latest material database: single START_MACHINE purge/prime profiles
# store not only E lengths, but also Z-Suite-observed feedrates F and areas.
# E_SPEED_SCALE scales these F values only; it does NOT change E lengths.
ZSUITE_START_SINGLE_E_FEED_PROFILES: dict[str, tuple[str, tuple[str, str, str], tuple[int, int, int]]] = {
    "Z-ABS": ("native Z-ABS single reference, observed legacy code 0x00", ("20.000", "20.802", "20.002"), (4800, 2200, 2200)),
    "Z-ULTRAT": ("native/external ULTRAT-based single reference", ("20.000", "21.020", "20.020"), (4800, 4400, 4400)),
    "Z-GLASS": ("native Z-GLASS / GLASS-type single reference", ("20.000", "22.000", "20.000"), (4800, 4800, 4800)),
    "Z-PETG": ("native Z-PETG single reference", ("20.000", "22.000", "20.000"), (4800, 4800, 4800)),
    "Z-PLA": ("LAB38-safe native Z-PLA single reference", ("20.000", "21.000", "20.000"), (4800, 2100, 2100)),
    "Z-PLA PRO": ("native Z-PLA Pro single reference", ("20.000", "21.504", "20.004"), (4800, 2100, 2100)),
    "Z-ASA PRO": ("native Z-ASA Pro / ASA Pro-based single reference", ("20.000", "21.000", "20.000"), (4800, 4400, 4400)),
    "Z-FLEX": ("native Z-FLEX single reference", ("20.000", "22.500", "20.000"), (4800, 2100, 2100)),
    "Z-NYLON": ("native Z-NYLON / NYLON-based single reference", ("20.000", "22.000", "20.000"), (4800, 4800, 4800)),
    "ABS-BASED FILAMENT": ("external ABS-based + Z-SUPPORT Premium reference", ("21.000", "22.000", "21.000"), (480, 2000, 2000)),
    "PETG-BASED FILAMENT": ("external PETG-based single reference", ("20.000", "22.000", "20.000"), (4800, 4800, 4800)),
    "GLASS-TYPE FILAMENT": ("external GLASS-type single reference", ("20.000", "22.000", "20.000"), (4800, 4800, 4800)),
    "PLA-BASED FILAMENT": ("external PLA-based single reference", ("20.000", "21.000", "20.000"), (4800, 2000, 2000)),
    "FLEX-BASED FILAMENT": ("external FLEX-based single reference", ("20.000", "22.500", "20.000"), (4800, 2100, 2100)),
    "NYLON-BASED FILAMENT": ("external NYLON-based single reference", ("20.000", "22.000", "20.000"), (4800, 4800, 4800)),
    "ULTRAT-BASED FILAMENT": ("external ULTRAT-based single reference", ("20.000", "21.020", "20.020"), (4800, 4400, 4400)),
    "ESD PETG-BASED FILAMENT": ("external ESD PETG-based single reference", ("20.000", "21.804", "20.004"), (4800, 4800, 4800)),
    "PLA PRO-BASED FILAMENT": ("external PLA Pro-based single reference", ("20.000", "21.504", "20.004"), (4800, 2100, 2100)),
    "ASA PRO-BASED FILAMENT": ("external ASA Pro-based single reference", ("20.000", "21.000", "20.000"), (4800, 4400, 4400)),
    "SEMIFLEX-BASED FILAMENT": ("external SEMIFLEX-based dual reference, code 0x96", ("22.020", "24.040", "22.040"), (480, 3600, 3600)),
}


ZSUITE_START_DUAL_E_PROFILES: dict[tuple[str, str], tuple[str, tuple[str, str, str]]] = {
    ("Z-PLA", "Z-SUPPORT"): ("dual Z-PLA + Z-SUPPORT reference", ("22.02", "24.04", "22.04")),
    ("Z-GLASS", "Z-SUPPORT PREMIUM"): ("dual Z-GLASS + Z-SUPPORT Premium reference", ("22.52", "25.04", "22.54")),
    ("Z-SEMIFLEX", "Z-SUPPORT PREMIUM"): ("dual Z-SEMIFLEX + Z-SUPPORT Premium reference", ("22.02", "24.04", "22.04")),
    ("Z-ULTRAT PLUS", "Z-SUPPORT PREMIUM"): ("dual Z-ULTRAT Plus + Z-SUPPORT Premium reference", ("21.00", "22.00", "21.00")),
    ("ABS-BASED FILAMENT", "Z-SUPPORT PREMIUM"): ("dual ABS-based + Z-SUPPORT Premium reference", ("21.00", "22.00", "21.00")),

    ("PLA-BASED FILAMENT", "Z-SUPPORT PREMIUM"): ("dual PLA-based + Z-SUPPORT Premium reference", ("22.02", "24.04", "22.04")),
    ("PETG-BASED FILAMENT", "Z-SUPPORT PREMIUM"): ("dual PETG-based + Z-SUPPORT Premium reference", ("22.02", "24.04", "22.04")),
    ("GLASS-TYPE FILAMENT", "Z-SUPPORT PREMIUM"): ("dual GLASS-type + Z-SUPPORT Premium reference", ("22.02", "24.04", "22.04")),
    ("SEMIFLEX-BASED FILAMENT", "Z-SUPPORT PREMIUM"): ("dual SEMIFLEX-based + Z-SUPPORT Premium reference", ("22.02", "24.04", "22.04")),
}
ZSUITE_START_DUAL_MODEL_FALLBACKS: dict[str, tuple[str, tuple[str, str, str]]] = {
    "Z-PLA": ("dual model-only fallback for Z-PLA", ("22.02", "24.04", "22.04")),
    "Z-GLASS": ("dual model-only fallback for Z-GLASS", ("22.52", "25.04", "22.54")),
    "Z-SEMIFLEX": ("dual model-only fallback for Z-SEMIFLEX", ("22.02", "24.04", "22.04")),
    "Z-ULTRAT PLUS": ("dual model-only fallback for Z-ULTRAT Plus", ("21.00", "22.00", "21.00")),
    "ABS-BASED FILAMENT": ("dual model-only fallback for ABS-based", ("21.00", "22.00", "21.00")),
}
ZSUITE_START_DUAL_E_FALLBACK = (
    "dual averaged fallback from references",
    ("21.85", "23.69", "21.86"),
)


# Dynamic Z-Suite-like START_MACHINE FW/bed profiles.
# These values are the leading firmware-start/material-prep parameters seen in
# original Z-Suite .zcode starts. They are kept separate from E-move profiles:
# FW values appear to encode material/bed/heat preparation, while E profiles
# encode purge/prime lengths.
ZSUITE_START_SINGLE_FW_PROFILES: dict[tuple[str, ...], dict[str, object]] = {
    ("Z-PLA",): {
        "source": "single Z-PLA FW/start reference",
        "fw_0e": 30, "fw_16": 30, "t0_fw": 210,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-FLEX",): {
        "source": "single Z-FLEX FW/start reference",
        "fw_0e": 40, "fw_16": 40, "t0_fw": 230,
        "zprep_1a": 0x02, "zprep_0610": 0,
        "tail_0315": False,
    },

    ("Z-ABS",): {
        "source": "native Z-ABS FW/start reference, observed legacy code 0x00",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 260,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-ULTRAT",): {
        "source": "native Z-ULTRAT / ULTRAT-based FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 260,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-GLASS",): {
        "source": "native Z-GLASS / GLASS-type FW/start reference",
        "fw_0e": 60, "fw_16": 60, "t0_fw": 225,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-PETG",): {
        "source": "native Z-PETG / PETG-based FW/start reference",
        "fw_0e": 60, "fw_16": 60, "t0_fw": 225,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-NYLON",): {
        "source": "native Z-NYLON / NYLON-based FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 250,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-ASA PRO",): {
        "source": "native Z-ASA Pro / ASA Pro-based FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 260,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-PLA PRO",): {
        "source": "native Z-PLA Pro / PLA Pro-based FW/start reference",
        "fw_0e": 30, "fw_16": 30, "t0_fw": 207,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("Z-FLEX",): {
        "source": "native Z-FLEX / FLEX-based FW/start reference",
        "fw_0e": 40, "fw_16": 40, "t0_fw": 230,
        "zprep_1a": 0x02, "zprep_0610": 0,
        "tail_0315": False,
    },
    ("ABS-BASED FILAMENT",): {
        "source": "external ABS-based FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 260,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("PETG-BASED FILAMENT",): {
        "source": "external PETG-based FW/start reference",
        "fw_0e": 60, "fw_16": 60, "t0_fw": 225,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("GLASS-TYPE FILAMENT",): {
        "source": "external GLASS-type FW/start reference",
        "fw_0e": 60, "fw_16": 60, "t0_fw": 225,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("PLA-BASED FILAMENT",): {
        "source": "external PLA-based FW/start reference",
        "fw_0e": 30, "fw_16": 30, "t0_fw": 210,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("FLEX-BASED FILAMENT",): {
        "source": "external FLEX-based FW/start reference",
        "fw_0e": 40, "fw_16": 40, "t0_fw": 230,
        "zprep_1a": 0x02, "zprep_0610": 0,
        "tail_0315": False,
    },
    ("NYLON-BASED FILAMENT",): {
        "source": "external NYLON-based FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 250,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("ULTRAT-BASED FILAMENT",): {
        "source": "external ULTRAT-based FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 260,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("ESD PETG-BASED FILAMENT",): {
        "source": "external ESD PETG-based FW/start reference",
        "fw_0e": 60, "fw_16": 60, "t0_fw": 270,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("PLA PRO-BASED FILAMENT",): {
        "source": "external PLA Pro-based FW/start reference",
        "fw_0e": 30, "fw_16": 30, "t0_fw": 207,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("ASA PRO-BASED FILAMENT",): {
        "source": "external ASA Pro-based FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t0_fw": 260,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
    ("SEMIFLEX-BASED FILAMENT",): {
        "source": "external SEMIFLEX-based dual reference",
        "fw_0e": 50, "fw_16": 50, "t0_fw": 225,
        "zprep_1a": 0x01, "zprep_0610": -8,
        "tail_0315": True,
    },
}
ZSUITE_START_SINGLE_FW_FALLBACK: dict[str, object] = {
    "source": "single averaged/default FW/start fallback",
    "fw_0e": 35, "fw_16": 35, "t0_fw": 220,
    "zprep_1a": 0x01, "zprep_0610": -8,
    "tail_0315": True,
}

ZSUITE_START_DUAL_FW_PROFILES: dict[tuple[str, str], dict[str, object]] = {
    ("Z-PLA", "Z-SUPPORT"): {
        "source": "dual Z-PLA + Z-SUPPORT FW/start reference",
        "fw_0e": 40, "fw_16": 40, "t1_fw": 220, "t0_fw": 90,
        "zprep_1a": 0x01, "zprep_0610": -6,
    },
    ("Z-GLASS", "Z-SUPPORT PREMIUM"): {
        "source": "dual Z-GLASS + Z-SUPPORT Premium FW/start reference",
        "fw_0e": 60, "fw_16": 60, "t1_fw": 220, "t0_fw": 60,
        "zprep_1a": 0x01, "zprep_0610": -5,
    },
    ("Z-SEMIFLEX", "Z-SUPPORT PREMIUM"): {
        "source": "dual Z-SEMIFLEX + Z-SUPPORT Premium FW/start reference",
        "fw_0e": 50, "fw_16": 50, "t1_fw": 220, "t0_fw": 90,
        "zprep_1a": 0x01, "zprep_0610": -5,
    },
    ("Z-ULTRAT PLUS", "Z-SUPPORT PREMIUM"): {
        "source": "dual Z-ULTRAT Plus + Z-SUPPORT Premium FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t1_fw": 220, "t0_fw": 90,
        "zprep_1a": 0x01, "zprep_0610": -6,
    },
    ("ABS-BASED FILAMENT", "Z-SUPPORT PREMIUM"): {
        "source": "dual ABS-based + Z-SUPPORT Premium FW/start reference",
        "fw_0e": 80, "fw_16": 80, "t1_fw": 230, "t0_fw": 90,
        "zprep_1a": 0x01, "zprep_0610": -6,
    },

    ("PLA-BASED FILAMENT", "Z-SUPPORT PREMIUM"): {
        "source": "dual PLA-based + Z-SUPPORT Premium reference",
        "fw_0e": 40, "fw_16": 40, "t1_fw": 220, "t0_fw": 210,
        "zprep_1a": 0x01, "zprep_0610": -5,
    },
    ("PETG-BASED FILAMENT", "Z-SUPPORT PREMIUM"): {
        "source": "dual PETG-based + Z-SUPPORT Premium reference",
        "fw_0e": 60, "fw_16": 60, "t1_fw": 220, "t0_fw": 235,
        "zprep_1a": 0x01, "zprep_0610": -5,
    },
    ("GLASS-TYPE FILAMENT", "Z-SUPPORT PREMIUM"): {
        "source": "dual GLASS-type + Z-SUPPORT Premium reference",
        "fw_0e": 60, "fw_16": 60, "t1_fw": 220, "t0_fw": 235,
        "zprep_1a": 0x01, "zprep_0610": -5,
    },
    ("SEMIFLEX-BASED FILAMENT", "Z-SUPPORT PREMIUM"): {
        "source": "dual SEMIFLEX-based + Z-SUPPORT Premium reference",
        "fw_0e": 50, "fw_16": 50, "t1_fw": 220, "t0_fw": 225,
        "zprep_1a": 0x01, "zprep_0610": -5,
    },
}
ZSUITE_START_DUAL_MODEL_FW_FALLBACKS: dict[str, dict[str, object]] = {
    "Z-PLA": ZSUITE_START_DUAL_FW_PROFILES[("Z-PLA", "Z-SUPPORT")],
    "Z-GLASS": ZSUITE_START_DUAL_FW_PROFILES[("Z-GLASS", "Z-SUPPORT PREMIUM")],
    "Z-SEMIFLEX": ZSUITE_START_DUAL_FW_PROFILES[("Z-SEMIFLEX", "Z-SUPPORT PREMIUM")],
    "Z-ULTRAT PLUS": ZSUITE_START_DUAL_FW_PROFILES[("Z-ULTRAT PLUS", "Z-SUPPORT PREMIUM")],
    "ABS-BASED FILAMENT": ZSUITE_START_DUAL_FW_PROFILES[("ABS-BASED FILAMENT", "Z-SUPPORT PREMIUM")],
}
ZSUITE_START_DUAL_FW_FALLBACK: dict[str, object] = {
    "source": "dual averaged/default FW/start fallback",
    "fw_0e": 54, "fw_16": 54, "t1_fw": 222, "t0_fw": 81,
    "zprep_1a": 0x01, "zprep_0610": -6,
}

ZS_T1_FAST_CLEAN_PASS_HEX = """
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 07 bf
06 02 20 1c 00 00 46
03 11 0a bd
06 02 20 1c 00 00 46
03 11 08 c2
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 07 bf
06 02 20 1c 00 00 46
03 11 00 eb
"""

ZS_START_SINGLE_TAIL_HEX = """
03 1a 67 c3
06 02 20 1c 00 00 46
"""

ZS_START_DUAL_TAIL_HEX = """
03 1a 67 c3
03 15 03 6d
06 02 20 1c 00 00 46
"""

ZS_CLEAN_SINGLE_HEX = """
06 02 20 1c 00 00 46
03 11 05 c0
06 02 20 1c 00 00 46
03 11 0a bd
06 02 20 1c 00 00 46
03 11 03 41
06 02 fa 00 00 00 25
03 11 01 3e
03 07 00 61
06 02 20 1c 00 00 46
03 11 00 eb
"""

ZS_CLEAN_DUAL_HEX = """
06 02 20 1c 00 00 46
03 11 06 6a
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 04 15
06 02 fa 00 00 00 25
03 11 02 94
03 07 01 b4
06 02 20 1c 00 00 46
03 11 00 eb
06 02 e0 01 00 00 d5
08 01 ea 08 93 52 00 00 b0
06 02 10 0e 00 00 ab
08 01 fe 08 26 5a 00 00 cd
06 0c b8 0b 00 00 5b
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 07 bf
06 02 20 1c 00 00 46
03 11 0a bd
06 02 20 1c 00 00 46
03 11 08 c2
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 07 bf
06 02 20 1c 00 00 46
03 11 00 eb
"""

ZS_END_SINGLE_HEX = """
07 08 00 00 00 00 00 78
03 05 03 dd
03 0b 64 d2
02 13 ee
08 01 ff 20 00 00 00 00 57
"""

ZS_END_DUAL_HEX = """
07 08 00 00 00 00 00 78
07 08 01 00 00 00 00 ce
03 05 03 dd
03 0b 64 d2
02 13 ee
08 01 ff 20 00 00 00 00 57
"""

def _zcmds_from_hex_blob(blob: str) -> list[bytes]:
    data = bytes.fromhex(blob)
    out: list[bytes] = []
    pos = 0
    while pos < len(data):
        length = data[pos]
        end = pos + length + 1
        if length < 2 or end > len(data):
            raise ValueError(f"Invalid embedded ZCode command blob at offset {pos}")
        out.append(data[pos:end])
        pos = end
    return out

ZS_START_SINGLE_BASE_SEQUENCE = _zcmds_from_hex_blob(ZS_START_SINGLE_BASE_HEX)
ZS_START_DUAL_STATIC_REFERENCE_SEQUENCE = _zcmds_from_hex_blob(ZS_START_DUAL_STATIC_REFERENCE_HEX)
# Up to and including CENTER_OVER_BIN_ACTIVE_TOOL (03 11 00 EB).
ZS_START_DUAL_BASE_SEQUENCE = ZS_START_DUAL_STATIC_REFERENCE_SEQUENCE[:28]
ZS_T1_FAST_CLEAN_PASS_SEQUENCE = _zcmds_from_hex_blob(ZS_T1_FAST_CLEAN_PASS_HEX)
ZS_START_SINGLE_TAIL_SEQUENCE = _zcmds_from_hex_blob(ZS_START_SINGLE_TAIL_HEX)
ZS_START_DUAL_TAIL_SEQUENCE = _zcmds_from_hex_blob(ZS_START_DUAL_TAIL_HEX)
ZS_START_MACHINE_SEQUENCES = {
    "SINGLE": list(ZS_START_SINGLE_BASE_SEQUENCE),
    "DUAL": list(ZS_START_DUAL_STATIC_REFERENCE_SEQUENCE),
}

ZS_CLEAN_MACHINE_SEQUENCES = {
    "SINGLE": _zcmds_from_hex_blob(ZS_CLEAN_SINGLE_HEX),
    "DUAL": _zcmds_from_hex_blob(ZS_CLEAN_DUAL_HEX),
}

ZS_END_MACHINE_SEQUENCES = {
    "SINGLE": _zcmds_from_hex_blob(ZS_END_SINGLE_HEX),
    "DUAL": _zcmds_from_hex_blob(ZS_END_DUAL_HEX),
}

# Z-Suite sets a normal feedrate immediately after the final GarbageCenter
# special-position command before returning from the cleaning area to model
# geometry. Without this restore, the first post-clean travel can inherit a
# slow cleaning/internal-motion feedrate on Inventure. These values come from
# the bunnydecor Z-Suite reference starts:
#   single: 06 02 c0 12 00 00 15 -> cmd 0x02, F4800
#   dual:   06 02 10 0e 00 00 ab -> cmd 0x02, F3600
ZS_POST_CLEAN_RESTORE_SINGLE = _zcmds_from_hex_blob("06 02 c0 12 00 00 15")
ZS_POST_CLEAN_RESTORE_DUAL = _zcmds_from_hex_blob("06 02 10 0e 00 00 ab")

def _fallback_zsuite_feedrate(mode: str, single_material: bool | None) -> int:
    key = _normalize_marker_token(mode or "AUTO")
    if key in {"AUTO", "CURRENT", "CURRENT_TOOL"}:
        return 4800 if single_material else 3600
    if key in {"SINGLE", "0", "TOOL0", "EXTRUDER0"}:
        return 4800
    if key in {"DUAL", "FULL_DUAL", "DUAL_FULL", "T0", "MODEL", "T1", "SUPPORT", "1", "TOOL1", "EXTRUDER1"}:
        return 3600
    return 3600

def _travel_feedrate_from_meta(meta: GCodeMetadata, mode: str = "AUTO") -> int:
    # Orca travel_speed is mm/s; ZCode feedrate command is mm/min.
    if meta.travel_feedrate and meta.travel_feedrate > 0:
        return int(meta.travel_feedrate)
    return _fallback_zsuite_feedrate(mode, meta.single_material)


def _mm_s_to_feedrate(v: Decimal | int | float | None) -> int | None:
    if v is None:
        return None
    try:
        d = Decimal(str(v))
    except Exception:
        return None
    if d <= 0:
        return None
    return int((d * Decimal(60)).to_integral_value(rounding=ROUND_HALF_UP))


def _tool_retract_feedrate_from_meta(meta: GCodeMetadata, tool: int, explicit_feedrate: int | None = None) -> int:
    if explicit_feedrate and explicit_feedrate > 0:
        return int(explicit_feedrate)
    f = _mm_s_to_feedrate(meta.retraction_speed_mm_s.get(int(tool)))
    return f if f is not None else 900


def _tool_deretract_feedrate_from_meta(meta: GCodeMetadata, tool: int, explicit_feedrate: int | None = None) -> int:
    if explicit_feedrate and explicit_feedrate > 0:
        return int(explicit_feedrate)
    # Orca convention: deretraction_speed = 0 means use retraction_speed.
    f = _mm_s_to_feedrate(meta.deretraction_speed_mm_s.get(int(tool)))
    if f is not None:
        return f
    return _tool_retract_feedrate_from_meta(meta, tool, None)

def zcmd_post_clean_restore_sequence(mode: str, meta: GCodeMetadata) -> list[bytes]:
    return [zcmd_simple(2, pack_i32(_travel_feedrate_from_meta(meta, mode)))]

def post_clean_min_feedrate(mode: str, meta: GCodeMetadata) -> int:
    return _travel_feedrate_from_meta(meta, mode)

def _machine_mode_key(mode: str, single_material: bool | None) -> str:
    key = _normalize_marker_token(mode or "AUTO")
    if key in {"AUTO", "CURRENT"}:
        return "SINGLE" if single_material else "DUAL"
    if key in {"0", "T0", "TOOL0", "EXTRUDER0", "SINGLE"}:
        return "SINGLE"
    if key in {"1", "T1", "TOOL1", "EXTRUDER1", "DUAL", "FULL_DUAL"}:
        return "DUAL"
    raise ValueError(f"Unknown Zortrax machine marker mode: {mode!r}")

def _canonical_material_from_code(code: int) -> str | None:
    preferred = {
        0x00: "Z-ABS", 0x01: "Z-ULTRAT", 0x02: "Z-GLASS", 0x03: "Z-HIPS", 0x04: "Z-PCABS",
        0x05: "Z-PETG", 0x06: "Z-ULTRAT PLUS", 0x07: "Z-SUPPORT",
        0x08: "Z-ESD", 0x09: "Z-PHA", 0x0A: "Z-PLA", 0x0B: "Z-PLA PRO",
        0x0C: "Z-ASA PRO", 0x0D: "Z-SUPPORT PLUS", 0x0E: "Z-SEMIFLEX",
        0x0F: "Z-FLEX", 0x10: "Z-NYLON", 0x11: "Z-SUPPORT PREMIUM", 0x13: "Z-SUPPORT ATP",
        0x12: "Z-PEEK", 0x17: "BASF ULTRAFUSE BVOH",
        0x81: "ABS-BASED FILAMENT", 0x83: "PETG-BASED FILAMENT",
        0x84: "GLASS-TYPE FILAMENT", 0x86: "PLA-BASED FILAMENT",
        0x87: "FLEX-BASED FILAMENT", 0x89: "NYLON-BASED FILAMENT",
        0x91: "ULTRAT-BASED FILAMENT", 0x92: "ESD PETG-BASED FILAMENT",
        0x94: "PLA PRO-BASED FILAMENT", 0x95: "ASA PRO-BASED FILAMENT",
        0x96: "SEMIFLEX-BASED FILAMENT",
    }
    return preferred.get(int(code or 0))


def _canonical_material_from_text(text: str | None) -> str | None:
    if not text:
        return None
    raw = str(text).strip()
    if not raw:
        return None
    candidates = [raw]
    candidates.extend(p.strip().strip('"\'[]') for p in re.split(r"[,;]", raw) if p.strip())
    for cand in candidates:
        norm = normalize_material_name(cand)
        alias = MATERIAL_ALIASES.get(norm, norm)
        if alias in MATERIAL_CODE_MAP:
            return alias
        code = material_code_from_name(cand)
        if code:
            resolved = _canonical_material_from_code(code)
            if resolved:
                return resolved
    return None


def _canonical_material_for_tool(meta: GCodeMetadata, tool: int) -> str | None:
    orca = getattr(meta, "orca_metadata", {}) or {}
    keys = [
        f"filament_t{tool}", f"filament_type_t{tool}", f"filament_settings_id_t{tool}",
        f"filament_settings_id[{tool}]", f"filament_type[{tool}]",
    ]
    if tool == 0:
        keys.extend(["filament_t0", "filament_type_t0", "filament_settings_id", "filament_type"])
    else:
        keys.extend(["filament_t1", "filament_type_t1"])
    for key in keys:
        found = _canonical_material_from_text(orca.get(key))
        if found:
            return found
    code = meta.model_code if tool == 0 else meta.support_code
    return _canonical_material_from_code(code)


def _choose_zsuite_start_e_profile(mode_key: str, meta: GCodeMetadata) -> tuple[str, tuple[Decimal, Decimal, Decimal]]:
    model = _canonical_material_for_tool(meta, 0)
    support = _canonical_material_for_tool(meta, 1)
    if mode_key == "SINGLE":
        if model and (model,) in ZSUITE_START_SINGLE_E_PROFILES:
            source, raw = ZSUITE_START_SINGLE_E_PROFILES[(model,)]
        else:
            source, raw = ZSUITE_START_SINGLE_E_FALLBACK
    else:
        if model and support and (model, support) in ZSUITE_START_DUAL_E_PROFILES:
            source, raw = ZSUITE_START_DUAL_E_PROFILES[(model, support)]
        elif model and model in ZSUITE_START_DUAL_MODEL_FALLBACKS:
            source, raw = ZSUITE_START_DUAL_MODEL_FALLBACKS[model]
        else:
            source, raw = ZSUITE_START_DUAL_E_FALLBACK
    d0, d1, d2 = (Decimal(x) for x in raw)
    return source, (d0, d1, d2)


def _feedrate_cmd(feedrate: int) -> bytes:
    return zcmd_simple(2, pack_i32(int(feedrate)))


def _scaled_feedrate(feedrate: int | float | Decimal | None, scale: object | None = None, minimum: int = 1) -> int:
    """Scale a ZCode feedrate (mm/min) defensively.

    Marker option E_SPEED_SCALE controls purge/prime E moves.
    Marker option RETRACT_SPEED_SCALE controls idle retract E moves.
    Non-E movement feedrates are intentionally not scaled.
    """
    if feedrate is None:
        return int(minimum)
    try:
        base = Decimal(str(feedrate))
    except Exception:
        return int(feedrate or minimum)
    try:
        sc = Decimal(str(scale)) if scale is not None else Decimal("1")
    except Exception:
        sc = Decimal("1")
    if sc <= 0:
        sc = Decimal("1")
    val = int((base * sc).to_integral_value(rounding=ROUND_HALF_UP))
    return max(int(minimum), val)


def _material_class_for_auto_scale(name: str | None) -> str:
    norm = normalize_material_name(name or "")
    if not norm:
        return "normal"
    if "BVOH" in norm or "PVA" in norm or "SUPPORT" in norm:
        return "brittle_support"
    if "FLEX" in norm or "SEMIFLEX" in norm:
        return "flex"
    return "normal"


def _auto_speed_scale_for_context(
    meta: GCodeMetadata | None = None,
    *,
    key: str = "e_speed_scale",
    tool: int | None = None,
    mode: str | None = None,
    default: Decimal | None = None,
) -> Decimal | None:
    """Resolve marker E_SPEED_SCALE=AUTO / RETRACT_SPEED_SCALE=AUTO.

    Scope: only Zortrax technical procedures generated by the converter:
    START_MACHINE, START_PURGE, TOOLCHANGE_CLEAN and LAYER_CLEAN.  This never
    changes normal print/process feedrates from Orca Process/G-code.

    Policy: explicit numeric marker value > AUTO material-class map > fallback.

    Conservative AUTO map:
    - support / BVOH / PVA / Z-SUPPORT family: 0.6;
    - FLEX / SEMIFLEX: 0.8;
    - normal model materials: 1.0.
    """
    if meta is None:
        return default
    names: list[str] = []
    if tool is not None:
        n = _canonical_material_for_tool(meta, int(tool))
        if n:
            names.append(n)
    else:
        for t in (0, 1):
            n = _canonical_material_for_tool(meta, t)
            if n:
                names.append(n)
    classes = {_material_class_for_auto_scale(n) for n in names}
    if "brittle_support" in classes:
        val = Decimal("0.6")
    elif "flex" in classes:
        val = Decimal("0.8")
    else:
        val = Decimal("1.0")
    diagnostic_print(f"[speed-policy] {key}=AUTO -> {val} ({'/'.join(names) or 'unknown'}; mode={mode or 'AUTO'})")
    return val


def _set_speed_scale_options_from_kv(opts: dict[str, object], kv: dict[str, str]) -> None:
    for key in ("E_SPEED_SCALE", "PURGE_SPEED_SCALE", "EXTRUSION_SPEED_SCALE", "PRIME_SPEED_SCALE"):
        if key in kv:
            raw = str(kv[key]).strip().upper()
            if raw == "AUTO":
                opts["e_speed_scale"] = "AUTO"
            else:
                try:
                    v = Decimal(str(kv[key]))
                    if v > 0:
                        opts["e_speed_scale"] = v
                except Exception:
                    pass
    for key in ("RETRACT_SPEED_SCALE", "IDLE_RETRACT_SPEED_SCALE", "RETRACTION_SPEED_SCALE"):
        if key in kv:
            raw = str(kv[key]).strip().upper()
            if raw == "AUTO":
                opts["retract_speed_scale"] = "AUTO"
            else:
                try:
                    v = Decimal(str(kv[key]))
                    if v > 0:
                        opts["retract_speed_scale"] = v
                except Exception:
                    pass


def _speed_scale_from_opts(
    opts: dict[str, object] | None,
    key: str,
    default: Decimal | None = None,
    *,
    meta: GCodeMetadata | None = None,
    tool: int | None = None,
    mode: str | None = None,
) -> Decimal | None:
    if not opts:
        return default
    val = opts.get(key)
    if val is None:
        return default
    if str(val).strip().upper() == "AUTO":
        return _auto_speed_scale_for_context(meta, key=key, tool=tool, mode=mode, default=default)
    try:
        dec = Decimal(str(val))
        return dec if dec > 0 else default
    except Exception:
        return default


def _parse_marker_mode_and_options(arg_text: str) -> tuple[str, dict[str, object]]:
    text = (arg_text or "").strip()
    if not text:
        return "AUTO", {}
    parts = text.split()
    mode = "AUTO"
    if parts and "=" not in parts[0]:
        mode = parts[0]
        parts = parts[1:]
    kv_raw = _parse_marker_key_values(" ".join(parts)) if parts else {}
    kv = {k.upper(): v for k, v in kv_raw.items()}
    opts: dict[str, object] = {}
    _set_speed_scale_options_from_kv(opts, kv)

    # v1.4.11/v1.2.16: optional manual temperature overrides in START_MACHINE.
    # These are intentionally higher priority than Z-Suite DB defaults, but lower
    # level marker-free Orca editing still works through ORCA METADATA.
    for key in ("CHAMBER", "CHAMBER_TEMP", "CHAMBER_TEMPERATURE", "BED", "BED_TEMP", "BED_TEMPERATURE"):
        if key in kv:
            parsed = _positive_int_from_text(kv[key])
            if parsed is not None:
                opts["chamber_temp"] = parsed
                break
    for key in ("T0_TEMP", "T0_TEMPERATURE", "MODEL_TEMP", "MODEL_TEMPERATURE"):
        if key in kv:
            parsed = _positive_int_from_text(kv[key])
            if parsed is not None:
                opts["t0_temp"] = parsed
                break
    for key in ("T1_TEMP", "T1_TEMPERATURE", "SUPPORT_TEMP", "SUPPORT_TEMPERATURE"):
        if key in kv:
            parsed = _positive_int_from_text(kv[key])
            if parsed is not None:
                opts["t1_temp"] = parsed
                break
    return mode, opts


def _e_move_cmd(extra: int, length_mm: Decimal) -> bytes:
    return zcmd_axis_with_values(1, {"E": Decimal(length_mm)}, int(extra))


def _restore_e_zero_cmd() -> bytes:
    return zcmd_simple(4, 0x08, pack_i32(0))



def _positive_int_from_text(value: object) -> int | None:
    """Parse a positive integer temperature from expanded Orca/Zortrax metadata.

    Orca sometimes leaves placeholders in preset dumps, e.g. ``{foo[0]}``; a
    naive regex would parse the ``0`` from ``[0]``.  For temperature overrides,
    unresolved placeholders must be ignored.
    """
    if value is None:
        return None
    text = str(value).strip().strip('"\'')
    if not text or "{" in text or "}" in text:
        return None
    dec = first_decimal(text)
    if dec is None or dec <= 0:
        return None
    try:
        return int(round(float(dec)))
    except Exception:
        try:
            return int(dec)
        except Exception:
            return None


def _meta_chamber_temp(meta: GCodeMetadata, *, initial: bool = True) -> int | None:
    """Return effective chamber temperature from Orca metadata.

    Policy:
    1. explicit job-level Zortrax/Inventure chamber metadata always overrides,
    2. Orca bed/plate temp can act as chamber only when it is unambiguous,
    3. in dual jobs with conflicting T0/T1 bed/chamber values, do not guess;
       keep the Z-Suite pair default unless CHAMBER=... or
       ; zortrax_chamber_temperature=... is supplied.
    """
    orca = getattr(meta, "orca_metadata", {}) or {}

    for key in (
        "zortrax_chamber_temperature",
        "zortrax_chamber_temp",
        "inventure_chamber_temperature",
        "inventure_chamber_temp",
    ):
        parsed = _positive_int_from_text(orca.get(key))
        if parsed is not None:
            diagnostic_print(f"[temp-policy] explicit job chamber from {key}={parsed}C")
            return parsed

    mode_text = str(orca.get("mode", "")).strip().upper()
    is_dual_job = mode_text == "DUAL" or bool(getattr(meta, "support_length_mm", 0) or 0)

    def pair_or_single(v0: int | None, v1: int | None, source: str) -> int | None:
        if is_dual_job:
            if v0 is not None and v1 is not None:
                if int(v0) == int(v1):
                    return int(v0)
                diagnostic_print(
                    f"[temp-policy] ignoring ambiguous dual {source}: "
                    f"T0={int(v0)}C, T1={int(v1)}C; use Z-Suite pair default or explicit CHAMBER=..."
                )
                return None
            # If dual but only one side is present, treat it as ambiguous too.
            if v0 is not None or v1 is not None:
                diagnostic_print(
                    f"[temp-policy] ignoring incomplete dual {source}: "
                    f"T0={v0}, T1={v1}; use explicit CHAMBER=... for manual override"
                )
                return None
            return None
        if v0 is not None:
            return int(v0)
        if v1 is not None:
            return int(v1)
        return None

    # Inventure: bed/plate temp in Orca can carry chamber temperature.  Use raw
    # T0/T1 metadata to detect dual conflicts instead of blindly taking T0.
    prefix = _plate_prefix_from_curr_bed_type(orca.get("curr_bed_type"))
    plate_prefixes = [prefix] if prefix else []
    for p in ("hot", "eng", "textured", "textured_cool", "cool", "supertack"):
        if p not in plate_prefixes:
            plate_prefixes.append(p)
    for p in plate_prefixes:
        if not p:
            continue
        base = f"bed_temp_{p}_initial" if initial else f"bed_temp_{p}"
        v0 = _positive_int_from_text(orca.get(f"{base}_t0"))
        v1 = _positive_int_from_text(orca.get(f"{base}_t1"))
        chosen = pair_or_single(v0, v1, base)
        if chosen is not None:
            return chosen

    # Fallback to explicit chamber metadata if user/preset uses Orca chamber fields.
    v0 = _positive_int_from_text(_orca_value_for_tool(orca, "chamber_temperature", 0))
    v1 = _positive_int_from_text(_orca_value_for_tool(orca, "chamber_temperature", 1))
    chosen = pair_or_single(v0, v1, "chamber_temperature")
    if chosen is not None:
        return chosen

    for key in ("chamber_temperature", "chamber_temp"):
        parsed = _positive_int_from_text(orca.get(key))
        if parsed is not None:
            return parsed
    return None


def _zsuite_start_fw_profile_with_orca_overrides(
    mode_key: str,
    meta: GCodeMetadata,
    profile: dict[str, object],
    opts: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return a copy of the Z-Suite FW profile with Orca/user temps applied.

    Policy: Z-Suite DB values are defaults.  Values edited in Orca and emitted
    in ORCA METADATA, or manual START_MACHINE CHAMBER/T0_TEMP/T1_TEMP options,
    are the values for this print and must override the DB.
    """
    out = dict(profile)
    opts = opts or {}
    notes: list[str] = []

    chamber = opts.get("chamber_temp") if isinstance(opts, dict) else None
    if chamber is None:
        chamber = _meta_chamber_temp(meta, initial=True)
    if chamber is not None and int(chamber) > 0:
        old0 = out.get("fw_0e")
        old16 = out.get("fw_16")
        out["fw_0e"] = int(chamber)
        out["fw_16"] = int(chamber)
        notes.append(f"chamber {old0}/{old16}-> {int(chamber)}C")

    t0 = opts.get("t0_temp") if isinstance(opts, dict) else None
    if t0 is None:
        t0 = _meta_tool_temp(meta, 0, initial=True)
    if t0 is not None and int(t0) > 0:
        old = out.get("t0_fw")
        out["t0_fw"] = int(t0)
        notes.append(f"T0 {old}-> {int(t0)}C")

    if mode_key == "DUAL":
        t1 = opts.get("t1_temp") if isinstance(opts, dict) else None
        if t1 is None:
            t1 = _meta_tool_temp(meta, 1, initial=True)
        if t1 is not None and int(t1) > 0:
            old = out.get("t1_fw")
            out["t1_fw"] = int(t1)
            notes.append(f"T1 {old}-> {int(t1)}C")

    if notes:
        out["source"] = f"{out.get('source', 'unknown FW/start profile')} + ORCA_OVERRIDES_ZSUITE_DEFAULTS ({'; '.join(notes)})"
        diagnostic_print("[temp-policy] ORCA_OVERRIDES_ZSUITE_DEFAULTS: " + "; ".join(notes))
    else:
        diagnostic_print("[temp-policy] Z-Suite DB defaults used; no Orca/user temperature override found")
    return out


def _choose_zsuite_start_fw_profile(mode_key: str, meta: GCodeMetadata) -> dict[str, object]:
    model = _canonical_material_for_tool(meta, 0)
    support = _canonical_material_for_tool(meta, 1)
    if mode_key == "SINGLE":
        if model and (model,) in ZSUITE_START_SINGLE_FW_PROFILES:
            return ZSUITE_START_SINGLE_FW_PROFILES[(model,)]
        return ZSUITE_START_SINGLE_FW_FALLBACK
    if model and support and (model, support) in ZSUITE_START_DUAL_FW_PROFILES:
        return ZSUITE_START_DUAL_FW_PROFILES[(model, support)]
    if model and model in ZSUITE_START_DUAL_MODEL_FW_FALLBACKS:
        return ZSUITE_START_DUAL_MODEL_FW_FALLBACKS[model]
    return ZSUITE_START_DUAL_FW_FALLBACK


def _cmd_fw_set_tool_value(tool: int, value: int) -> bytes:
    # Reference shape: 07 08 <tool> <int32> <crc>
    return zcmd_simple(0x08, int(tool), pack_i32(int(value)))


def _zsuite_fw_start_sequence(mode_key: str, profile: dict[str, object]) -> list[bytes]:
    cmds = [
        bytes.fromhex("03 0B 00 15"),
        bytes.fromhex("07 04 08 00 00 00 00 C2"),
        bytes.fromhex("08 01 FF 10 00 00 00 00 A7"),
        zcmd_simple(0x0E, pack_i32(int(profile["fw_0e"]))),
        zcmd_simple(0x16, pack_i32(int(profile["fw_16"]))),
    ]
    if mode_key == "DUAL":
        cmds.append(_cmd_fw_set_tool_value(1, int(profile["t1_fw"])))
    cmds.append(_cmd_fw_set_tool_value(0, int(profile["t0_fw"])))
    cmds.append(bytes.fromhex("02 14 BA"))
    return cmds


def _zsuite_home_xy_z_sequence() -> list[bytes]:
    return [bytes.fromhex("03 05 03 DD"), bytes.fromhex("03 05 04 89")]


def _zsuite_bed_z_prep_sequence(profile: dict[str, object]) -> list[bytes]:
    return [
        bytes.fromhex("0F 04 07 00 00 00 00 00 00 00 00 00 00 00 00 C3"),
        _feedrate_cmd(180),
        bytes.fromhex("08 01 FF 04 FE 2E 00 00 30"),
        zcmd_simple(0x1C, pack_i32(0)),
        zcmd_simple(0x1A, int(profile["zprep_1a"])),
        zcmd_simple(0x10, pack_i32(int(profile["zprep_0610"]))),
        zcmd_simple(0x1A, 0x03),
    ]


def _zsuite_switch_t0_start_sequence() -> list[bytes]:
    return _zcmds_from_hex_blob("""
06 02 20 1c 00 00 46
03 11 05 c0
06 02 20 1c 00 00 46
03 11 0a bd
06 02 20 1c 00 00 46
03 11 03 41
06 02 fa 00 00 00 25
03 11 01 3e
03 07 00 61
06 02 20 1c 00 00 46
03 11 00 eb
""")


def _zsuite_switch_t1_start_sequence() -> list[bytes]:
    return _zcmds_from_hex_blob("""
06 02 20 1c 00 00 46
03 11 06 6a
06 02 20 1c 00 00 46
03 11 09 17
06 02 20 1c 00 00 46
03 11 04 15
06 02 fa 00 00 00 25
03 11 02 94
03 07 01 b4
06 02 20 1c 00 00 46
03 11 00 eb
""")


def _zsuite_single_tail_sequence(profile: dict[str, object]) -> list[bytes]:
    # Z-FLEX references continue directly after CMD_1A_67; Z-PLA references include CMD_15_03.
    cmds = [bytes.fromhex("03 1A 67 C3")]
    if bool(profile.get("tail_0315", True)):
        cmds.append(bytes.fromhex("03 15 03 6D"))
    cmds.append(_feedrate_cmd(7200))
    return cmds


def _zsuite_dual_tail_sequence() -> list[bytes]:
    return [bytes.fromhex("03 1A 67 C3"), bytes.fromhex("03 15 03 6D"), _feedrate_cmd(7200)]


def _zsuite_start_base_sequence(mode_key: str, meta: GCodeMetadata, speed_opts: dict[str, object] | None = None) -> tuple[str, list[bytes], dict[str, object]]:
    profile = _choose_zsuite_start_fw_profile(mode_key, meta)
    profile = _zsuite_start_fw_profile_with_orca_overrides(mode_key, meta, profile, speed_opts)
    cmds: list[bytes] = []
    cmds.extend(_zsuite_fw_start_sequence(mode_key, profile))
    cmds.extend(_zsuite_home_xy_z_sequence())
    cmds.extend(_zsuite_bed_z_prep_sequence(profile))
    if mode_key == "SINGLE":
        cmds.extend(_zsuite_switch_t0_start_sequence())
    else:
        cmds.extend(_zsuite_switch_t1_start_sequence())
    return str(profile.get("source", "unknown FW/start profile")), cmds, profile


def _zsuite_single_start_dynamic_sequence(meta: GCodeMetadata, speed_opts: dict[str, object] | None = None) -> list[bytes]:
    e_source, moves = _choose_zsuite_start_e_profile("SINGLE", meta)
    single_feeds = (4800, 2100, 2100)
    model_for_feed = _canonical_material_for_tool(meta, 0)
    if model_for_feed and model_for_feed in ZSUITE_START_SINGLE_E_FEED_PROFILES:
        e_source, raw_moves, single_feeds = ZSUITE_START_SINGLE_E_FEED_PROFILES[model_for_feed]
        moves = tuple(Decimal(x) for x in raw_moves)  # type: ignore[assignment]
    fw_source, cmds, fw_profile = _zsuite_start_base_sequence("SINGLE", meta, speed_opts)
    # Z-Suite SINGLE: FW start/basket/heat -> HOME XY/Z -> bed/Z prep -> switch T0 -> center -> E1/E2/E3 -> restore E.
    # There is no explicit fast-clean path in confirmed Z-Suite SINGLE starts.
    # v1.2.3: after the firmware start/preheat block and immediately before purge/prime,
    # force the Orca material temperature. This prevents low FW-profile values from
    # underheating high-temperature materials.
    cmds.extend(_emit_tool_orca_temp(meta, 0, initial=True, wait=True))
    e_scale = _speed_scale_from_opts(speed_opts, "e_speed_scale", meta=meta, tool=0, mode="START_MACHINE_SINGLE")
    f0 = _scaled_feedrate(single_feeds[0], e_scale)
    f1 = _scaled_feedrate(single_feeds[1], e_scale)
    f2 = _scaled_feedrate(single_feeds[2], e_scale)
    cmds.extend([
        _feedrate_cmd(f0),
        _e_move_cmd(0xFE, moves[0]),
        _feedrate_cmd(f1),
        _e_move_cmd(0xFE, moves[1]),
    ])
    if f2 != f1:
        cmds.append(_feedrate_cmd(f2))
    cmds.extend([
        _e_move_cmd(0xFD, moves[2]),
        _restore_e_zero_cmd(),
    ])
    cmds.extend(_zsuite_single_tail_sequence(fw_profile))
    diagnostic_print(f"[start-profile] SINGLE FW={fw_source}; E={e_source}: E moves {moves[0]} / {moves[1]} / {moves[2]} mm; F={single_feeds[0]}/{single_feeds[1]}/{single_feeds[2]}")
    return cmds


def _zsuite_dual_start_dynamic_sequence(meta: GCodeMetadata, speed_opts: dict[str, object] | None = None) -> list[bytes]:
    e_source, moves = _choose_zsuite_start_e_profile("DUAL", meta)
    fw_source, cmds, _fw_profile = _zsuite_start_base_sequence("DUAL", meta, speed_opts)
    # Z-Suite DUAL: FW start/basket/heat -> HOME XY/Z -> bed/Z prep -> switch T1 -> center ->
    # pre-clean E moves -> dwell -> explicit T1 fast-clean path -> post-clean E move -> restore E.
    # v1.2.3: restore actual Orca material temperatures for both extruders after
    # the FW start/preheat block. The old FW profile can keep T0 at e.g. 60/90C,
    # which is too low for ABS or other high-temperature model materials.
    cmds.extend(_emit_tool_orca_temp(meta, 0, initial=True, wait=False))
    cmds.extend(_emit_tool_orca_temp(meta, 1, initial=True, wait=True))
    e_scale = _speed_scale_from_opts(speed_opts, "e_speed_scale", meta=meta, tool=1, mode="START_MACHINE_DUAL")
    cmds.extend([
        _feedrate_cmd(_scaled_feedrate(480, e_scale)),
        _e_move_cmd(0xEA, moves[0]),
        _feedrate_cmd(_scaled_feedrate(3600, e_scale)),
        _e_move_cmd(0xFE, moves[1]),
        zcmd_simple(12, pack_i32(3000)),
    ])
    cmds.extend(ZS_T1_FAST_CLEAN_PASS_SEQUENCE)
    cmds.extend([
        _feedrate_cmd(_scaled_feedrate(3600, e_scale)),
        _e_move_cmd(0xFD, moves[2]),
        _restore_e_zero_cmd(),
    ])
    cmds.extend(_zsuite_dual_tail_sequence())
    diagnostic_print(f"[start-profile] DUAL FW={fw_source}; E={e_source}: E moves {moves[0]} / {moves[1]} / {moves[2]} mm")
    return cmds


# ---------------------------------------------------------------------------
# Optional shortened pre-print load-like procedure
# ---------------------------------------------------------------------------
# These sequences are based on real-printer tests of the old T1->T0 context that
# intentionally triggered the firmware load-like / long-wait / clean behavior.
# They are intentionally NOT used by START_MACHINE by default.  Use explicit
# markers only:
#   ;ZORTRAX_LOAD_FILAMENT T0
#   ;ZORTRAX_LOAD_FILAMENT T1
#   ;ZORTRAX_LOAD_FILAMENT AUTO     # SINGLE -> T0, DUAL -> T0 then T1
#   ;ZORTRAX_LOAD_FILAMENT BOTH
# The key trigger remains: old-tool -20 mm retract without immediate RESTORE,
# then SELECT new tool, then fast FE/FE, clean path, FD, RESTORE.  A safe
# post-park RESTORE is emitted by default after the final T0/T1 park.

def _load_marker_bool(opts: dict[str, str], key: str, default: bool = True) -> bool:
    val = opts.get(key.upper())
    if val is None:
        return bool(default)
    parsed = parse_bool(str(val))
    return bool(default) if parsed is None else bool(parsed)


def _load_marker_temp(meta: GCodeMetadata, tool: int, opts: dict[str, str]) -> int:
    # Explicit marker override wins; otherwise use actual Orca value; fallback to
    # 220C because the confirmed tests used 220C-class material temperatures.
    key_sets = (
        ("T0_TEMP", "MODEL_TEMP", "TEMP0") if int(tool) == 0 else ("T1_TEMP", "SUPPORT_TEMP", "TEMP1")
    )
    for k in key_sets:
        if k in opts and str(opts[k]).strip().upper() != "AUTO":
            parsed = _positive_int_from_text(opts[k])
            if parsed is not None:
                return int(parsed)
    val = _meta_tool_temp(meta, int(tool), initial=True) or _meta_tool_temp(meta, int(tool), initial=False)
    return int(val) if val is not None and int(val) > 0 else 220


def _load_marker_standby_temp(meta: GCodeMetadata, inactive_tool: int, opts: dict[str, str]) -> int:
    # The old confirmed load-like fragments used a shallow standby around
    # active-4C (e.g. 220 -> 216), not the normal ooze-prevention -20C.
    explicit = opts.get("STANDBY_TEMP") or opts.get("IDLE_TEMP")
    if explicit is not None and str(explicit).strip().upper() != "AUTO":
        parsed = _positive_int_from_text(explicit)
        if parsed is not None:
            return int(parsed)
    active = _meta_tool_temp(meta, int(inactive_tool), initial=True) or _meta_tool_temp(meta, int(inactive_tool), initial=False) or 220
    return max(0, int(active) - 4)


def _select_tool_cmd(tool: int) -> bytes:
    return bytes.fromhex("03 07 00 61") if int(tool) == 0 else bytes.fromhex("03 07 01 B4")


def _loadlike_t0_sequence(meta: GCodeMetadata, opts: dict[str, str]) -> list[bytes]:
    """Confirmed shortened load-like procedure for loading/cleaning T0.

    Assumes/creates the old-tool T1 -> new-tool T0 context.  The missing
    RESTORE after E -20 area F3 is intentional; final RESTORE after park is safe.
    """
    park = _load_marker_bool(opts, "PARK", True)
    post_restore = _load_marker_bool(opts, "POST_RESTORE", True)
    temp_mode = str(opts.get("TEMP", "AUTO")).strip().upper()
    t0_temp = _load_marker_temp(meta, 0, opts)
    t1_standby = _load_marker_standby_temp(meta, 1, opts)
    out: list[bytes] = []
    if temp_mode != "OFF":
        out.extend(_emit_tool_temperature(0, t0_temp, wait=False))
    out.extend([
        _feedrate_cmd(7200), zcmd_special_position(0x05),
        _feedrate_cmd(7200), zcmd_special_position(0x0A),
        _feedrate_cmd(480), _e_move_cmd(0xF3, Decimal("-20.000")),
        # Intentionally no RESTORE E0 here: this is the confirmed trigger context.
        _feedrate_cmd(7200), zcmd_special_position(0x03),
        _feedrate_cmd(250), zcmd_special_position(0x01),
        _select_tool_cmd(0),
    ])
    if temp_mode != "OFF":
        out.extend(_emit_tool_temperature(1, t1_standby, wait=False))
        out.extend(_emit_tool_temperature(0, t0_temp, wait=False))
        out.append(bytes.fromhex("02 14 BA"))
    out.extend([
        _feedrate_cmd(7200), zcmd_special_position(0x00),
        _feedrate_cmd(4800), _e_move_cmd(0xFE, Decimal("20.000")),
        _feedrate_cmd(2100), _e_move_cmd(0xFE, Decimal("21.000")),
    ])
    out.extend(_clean_path_for_tool(0))
    out.extend([
        _e_move_cmd(0xFD, Decimal("20.000")),
        _restore_e_zero_cmd(),
    ])
    if park:
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x09)])
    if post_restore:
        out.append(_restore_e_zero_cmd())
    diagnostic_print(f"[load-filament] T0 shortened load-like sequence emitted; T0={t0_temp}C, T1_standby={t1_standby}C, park={park}, post_restore={post_restore}")
    return out


def _loadlike_t1_sequence(meta: GCodeMetadata, opts: dict[str, str]) -> list[bytes]:
    """Confirmed shortened load-like procedure for loading/cleaning T1.

    Creates old-tool T0 -> new-tool T1 context via SELECT T0, then intentionally
    omits RESTORE after E -20 area E9.  Final RESTORE after park is safe.
    """
    park = _load_marker_bool(opts, "PARK", True)
    post_restore = _load_marker_bool(opts, "POST_RESTORE", True)
    temp_mode = str(opts.get("TEMP", "AUTO")).strip().upper()
    t1_temp = _load_marker_temp(meta, 1, opts)
    t0_standby = _load_marker_standby_temp(meta, 0, opts)
    out: list[bytes] = [
        _select_tool_cmd(0),
    ]
    if temp_mode != "OFF":
        out.extend(_emit_tool_temperature(1, t1_temp, wait=False))
    out.extend([
        _feedrate_cmd(7200), zcmd_special_position(0x06),
        _feedrate_cmd(7200), zcmd_special_position(0x09),
        _feedrate_cmd(480), _e_move_cmd(0xE9, Decimal("-20.000")),
        # Intentionally no RESTORE E0 here: this is the confirmed trigger context.
        _feedrate_cmd(7200), zcmd_special_position(0x04),
        _feedrate_cmd(250), zcmd_special_position(0x02),
        _select_tool_cmd(1),
    ])
    if temp_mode != "OFF":
        out.extend(_emit_tool_temperature(0, t0_standby, wait=False))
        out.extend(_emit_tool_temperature(1, t1_temp, wait=False))
        out.append(bytes.fromhex("02 14 BA"))
    out.extend([
        _feedrate_cmd(7200), zcmd_special_position(0x00),
        _feedrate_cmd(4800), _e_move_cmd(0xFE, Decimal("20.000")),
        _feedrate_cmd(2100), _e_move_cmd(0xFE, Decimal("21.000")),
    ])
    out.extend(_clean_path_for_tool(1))
    out.extend([
        _e_move_cmd(0xFD, Decimal("20.000")),
        _restore_e_zero_cmd(),
    ])
    if park:
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x0A)])
    if post_restore:
        out.append(_restore_e_zero_cmd())
    diagnostic_print(f"[load-filament] T1 shortened load-like sequence emitted; T1={t1_temp}C, T0_standby={t0_standby}C, park={park}, post_restore={post_restore}")
    return out


def zcmd_load_filament_sequence(marker_args: str, meta: GCodeMetadata, st: AxisState | None = None) -> list[bytes]:
    tokens = marker_args.strip().split()
    mode = "AUTO"
    if tokens and "=" not in tokens[0]:
        mode = tokens[0]
        tokens = tokens[1:]
    opts = {str(k).upper(): str(v) for k, v in _parse_marker_key_values(" ".join(tokens)).items()}
    key = _normalize_marker_token(mode or "AUTO")
    if key in {"0", "T0", "TOOL0", "EXTRUDER0", "MODEL"}:
        tools = [0]
    elif key in {"1", "T1", "TOOL1", "EXTRUDER1", "SUPPORT"}:
        tools = [1]
    elif key in {"BOTH", "DUAL", "ALL", "T0_T1", "T0T1"}:
        tools = [0, 1]
    elif key in {"AUTO", "CURRENT"}:
        tools = [0] if bool(getattr(meta, "single_material", False)) else [0, 1]
    else:
        raise ValueError(f"Unknown ZORTRAX_LOAD_FILAMENT mode: {mode!r}")
    out: list[bytes] = []
    for tool in tools:
        out.extend(_loadlike_t0_sequence(meta, opts) if int(tool) == 0 else _loadlike_t1_sequence(meta, opts))
        if st is not None:
            st.active_extruder = int(tool)
            st.cleaned_tools.add(int(tool))
    return out

def zcmd_start_machine_sequence(mode: str, meta: GCodeMetadata) -> list[bytes]:
    # v1.2.7: marker may include speed options, e.g.
    # ;ZORTRAX_START_MACHINE DUAL E_SPEED_SCALE=0.5
    mode_token, speed_opts = _parse_marker_mode_and_options(mode)
    mode_key = _machine_mode_key(mode_token, meta.single_material)
    if mode_key == "SINGLE":
        return _zsuite_single_start_dynamic_sequence(meta, speed_opts)
    return _zsuite_dual_start_dynamic_sequence(meta, speed_opts)

def zcmd_end_machine_sequence(mode: str, single_material: bool | None) -> list[bytes]:
    return list(ZS_END_MACHINE_SEQUENCES[_machine_mode_key(mode, single_material)])

def marker_final_active_tool(mode: str, single_material: bool | None, current_tool: int = 0) -> int:
    """Return the active tool implied by embedded Z-Suite machine/clean sequences.

    Z-Suite dual start/clean sequences used here end on support tool T1.
    Single sequences end on model tool T0. Explicit T0/T1 markers set that tool.
    AUTO follows single/dual metadata, while CURRENT leaves current_tool.
    """
    key = _normalize_marker_token(mode or "AUTO")
    if key in {"CURRENT", "CURRENT_TOOL"}:
        return current_tool
    if key == "AUTO":
        return 0 if single_material else 1
    if key in {"SINGLE", "0", "T0", "TOOL0", "EXTRUDER0", "MODEL"}:
        return 0
    if key in {"DUAL", "FULL_DUAL", "DUAL_FULL", "1", "T1", "TOOL1", "EXTRUDER1", "SUPPORT"}:
        return 1
    return current_tool

# ---------------------------------------------------------------------------
# Orca / G-code preprocessing
# ---------------------------------------------------------------------------

def normalize_leading_zero_text(text: str) -> str:
    text = re.sub(r'(?<![A-Za-z0-9_])([A-Za-z])\.(\d)', r'\g<1>0.\2', text)
    text = re.sub(r'(?<![A-Za-z0-9_])([A-Za-z])-?\.(\d)', lambda m: f"{m.group(1)}-0.{m.group(2)}" if '-' in m.group(0) else f"{m.group(1)}0.{m.group(2)}", text)
    text = re.sub(r'([A-Za-z])-\.(\d)', r'\1-0.\2', text)
    return text


_float_token = re.compile(r'([XYZEFABRSTP])\s*([-+]?\d*\.?\d+)')

def _format_float(val: float) -> str:
    s = f"{val:.5f}".rstrip("0").rstrip(".")
    return "0" if s in {"", "-0"} else s


def _replace_or_append_e(main: str, e_val: float) -> str:
    if re.search(r'(^|\s)E[-+]?\d*\.?\d+', main):
        return re.sub(r'(^|\s)E[-+]?\d*\.?\d+', lambda m: f"{m.group(1)}E{_format_float(e_val)}", main, count=1)
    return main + f" E{_format_float(e_val)}"


def convert_relative_e_to_orca_like_m82(text: str) -> str:
    """
    Conservative work-copy transform used by the latest wrapper logic:
    - turn M83 regions into M82 style,
    - keep original G92 E0 resets,
    - after pure-E retract/unretract moves emit a synthetic G92 E0 and reset the
      absolute counter, matching the proven 'Orca-like M82' pattern.
    """
    out: list[str] = []
    relative_e = False
    e_abs = 0.0

    for raw in text.splitlines():
        if ";" in raw:
            main, comment = raw.split(";", 1)
            comment = ";" + comment
        else:
            main, comment = raw, ""
        stripped = main.strip()

        if re.match(r'^M83\b', stripped):
            relative_e = True
            out.append(re.sub(r'^(\s*)M83\b', r'\1M82', main) + comment)
            continue
        if re.match(r'^M82\b', stripped):
            relative_e = False
            out.append(raw)
            continue
        if re.match(r'^G92\b', stripped):
            m = re.search(r'(^|\s)E([-+]?\d*\.?\d+)', main)
            if m:
                try:
                    e_abs = float(m.group(2))
                except ValueError:
                    e_abs = 0.0
            out.append(raw)
            continue

        if relative_e and re.match(r'^(G0|G1)\b', stripped):
            params = dict((k, v) for k, v in _float_token.findall(main))
            if "E" in params:
                try:
                    e_delta = float(params["E"])
                except ValueError:
                    out.append(raw)
                    continue
                e_abs += e_delta
                new_main = _replace_or_append_e(main, e_abs)
                out.append(new_main + comment)

                has_xyz = any(axis in params for axis in ("X", "Y", "Z"))
                if not has_xyz:
                    out.append("G92 E0 ; reset extrusion distance (synthetic after converted relative-E move)")
                    e_abs = 0.0
                continue

        out.append(raw)

    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def maybe_prepare_working_gcode(input_path: Path, preserve_temp: bool = False) -> tuple[Path, Path | None, bool]:
    text = input_path.read_text(encoding="utf-8", errors="ignore")
    normalized = normalize_leading_zero_text(text)
    needs_m83_fix = bool(re.search(r'^\s*M83\b', normalized, flags=re.M))
    if needs_m83_fix:
        normalized = convert_relative_e_to_orca_like_m82(normalized)

    if normalized == text and input_path.suffix.lower() == ".gcode":
        return input_path, None, needs_m83_fix

    temp_dir = Path(tempfile.mkdtemp(prefix="orca_py_zcode_"))
    work_path = temp_dir / (input_path.stem.replace(".gcode", "") + ".gcode")
    with open(work_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(normalized)
    if preserve_temp:
        console_print(f"[debug] work copy: {work_path}")
    return work_path, temp_dir, needs_m83_fix

# ---------------------------------------------------------------------------
# Pure-Python classic ZCode generator
# ---------------------------------------------------------------------------

def pack_i32(v: int) -> bytes:
    return int(v).to_bytes(4, "little", signed=True)

def zcmd_simple(cmd: int, *parts: bytes | int) -> bytes:
    payload_len = sum(len(p) if isinstance(p, (bytes, bytearray)) else 1 for p in parts)
    arr = bytearray([2 + payload_len, cmd & 0xFF])
    for p in parts:
        if isinstance(p, (bytes, bytearray)):
            arr.extend(p)
        else:
            arr.append(int(p) & 0xFF)
    arr.append(crc8_d5(bytes(arr)))
    return bytes(arr)

def half_up_round_int(value: Decimal | float | int) -> int:
    v = float(value)
    if v >= 0:
        return int(math.floor(v + 0.5))
    return int(math.ceil(v - 0.5))

def convert_steps(vals: dict[str, Decimal | None]) -> dict[str, int]:
    out: dict[str, int] = {}
    for k, v in vals.items():
        if v is None:
            continue
        mult = STEPS[k]
        if mult == 0:
            out[k] = 0
        else:
            out[k] = half_up_round_int(float(v) * mult)
    return out

def bitfield(vals: dict[str, int]) -> int:
    out = 0
    for k, m in [("X", 1), ("Y", 2), ("Z", 4), ("E", 8), ("A", 16), ("B", 32), ("Z2", 64)]:
        if vals.get(k) is not None:
            out |= m
    return out

def axis_values_bytes(vals: dict[str, int]) -> bytes:
    ba = bytearray()
    for k in ["X", "Y", "Z", "E", "A", "B", "Z2"]:
        if vals.get(k) is not None:
            ba.extend(pack_i32(vals[k]))
    return bytes(ba)

def zcmd_axis(cmd: int, vals: dict[str, Decimal | None]) -> bytes:
    ivals = convert_steps(vals)
    arr = bytearray([3, cmd & 0xFF, bitfield(ivals)])
    arr.append(crc8_d5(bytes(arr)))
    return bytes(arr)

def zcmd_axis_with_values(cmd: int, vals: dict[str, Decimal | None], *extras: int) -> bytes:
    ivals = convert_steps(vals)
    vb = axis_values_bytes(ivals)
    arr = bytearray([3 + len(extras) + len(vb), cmd & 0xFF])
    for e in extras:
        arr.append(int(e) & 0xFF)
    arr.append(bitfield(ivals))
    arr.extend(vb)
    arr.append(crc8_d5(bytes(arr)))
    return bytes(arr)

class AxisState:
    def __init__(self) -> None:
        self.relative = False
        self.relative_e = False
        self.device_relative = False
        self.device_relative_e = False
        self.active_extruder = 0
        # v6: active tool and cleaned/prepared tool are separate states.
        # Dual Z-Suite start leaves T1 active/prepared, while T0 can still
        # need its first-use clean later.
        self.cleaned_tools: set[int] = set()
        self.pending_clean_tool: int | None = None
        self.pending_clean_mode: str | None = None
        self.pending_clean_purge_mm: Decimal | None = None
        self.pending_clean_purge_f: int | None = None
        self.pending_idle_retract_mm: Decimal | None = None
        self.pending_idle_retract_f: int | None = None
        # Tracks physical idle retraction per tool. The converter restores logical E after each
        # idle retract/unretract, so this is only tool-preparation state.
        self.idle_retracted_mm: dict[int, Decimal] = {0: Decimal(0), 1: Decimal(0)}
        self.current = {"X": Decimal(0), "Y": Decimal(0), "Z": Decimal(0), "E": Decimal(0)}
        # Current layer index for optional cleaning intervals.
        self.current_layer: int = 0
        # LAB05: Z-Suite Layer opcode / PrintingArea tracking for viewer tests.
        self.zsuite_layer_index: int = -1
        self.current_orca_type: str = ""
        self.current_area: int = UNKNOWN_PRINTING_AREA
        # v1.2.6: layer-clean can skip the layer immediately following a
        # ZORTRAX_TOOLCHANGE_CLEAN to avoid duplicate purge/prime.
        self.last_toolchange_clean_layer: int | None = None
        self.toolchange_clean_skip_pending: bool = False
        self.pending_post_clean_min_feedrate: int | None = None
        self.pending_toolchange_meta: dict[str, str] = {}
        # v1.2.8/v1.4.1: after ZORTRAX_TOOLCHANGE_CLEAN the next Orca M109 for
        # the same tool is duplicate. The clean marker already waited at the
        # correct temperature before purge/brush clean.
        self.skip_next_post_toolchange_m109_tool: int | None = None

    def fix(self, axis: str, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        rel = self.relative_e if axis == "E" else self.relative
        dev = self.device_relative_e if axis == "E" else self.device_relative
        key = "E" if axis == "E" else axis

        if rel == dev:
            if rel:
                self.current[key] += value
                return value
            self.current[key] = value
            return value

        if rel and not dev:
            self.current[key] += value
            return self.current[key]

        out = value - self.current[key]
        self.current[key] = value
        return out

def parse_line(raw: str) -> tuple[str | None, str | None, dict[str, Decimal]]:
    s = raw.strip()
    if not s:
        return None, None, {}
    if s.startswith(";"):
        return "COMMENT", s[1:].strip(), {}
    main = s.split(";", 1)[0].strip()
    if not main:
        return None, None, {}
    m = re.match(r'([GMT]\d+|T\d+)\b(.*)', main)
    if not m:
        return None, None, {}
    cmd = m.group(1)
    rest = m.group(2).strip()
    params = {k: Decimal(v) for k, v in re.findall(r'([A-Za-z])\s*([-+]?\d*\.?\d+)', rest)}
    return cmd, None, params

def _no_progress_inside_command_set() -> set[bytes]:
    """Commands that should remain contiguous exactly as Z-Suite emits them."""
    no_progress: set[bytes] = set()
    try:
        for seq in ZS_START_MACHINE_SEQUENCES.values():
            no_progress.update(seq)
        # v1.03: START_MACHINE is now partly dynamic by material.  Add all
        # known/generated Z-Suite start variants so progress opcodes are not
        # injected inside the firmware start / purge / clean procedure.
        start_fw_profiles = list(ZSUITE_START_SINGLE_FW_PROFILES.values()) + [ZSUITE_START_SINGLE_FW_FALLBACK]
        start_fw_profiles += list(ZSUITE_START_DUAL_FW_PROFILES.values()) + [ZSUITE_START_DUAL_FW_FALLBACK]
        for prof in start_fw_profiles:
            mode_key = "DUAL" if "t1_fw" in prof else "SINGLE"
            no_progress.update(_zsuite_fw_start_sequence(mode_key, prof))
            no_progress.update(_zsuite_home_xy_z_sequence())
            no_progress.update(_zsuite_bed_z_prep_sequence(prof))
            if mode_key == "SINGLE":
                no_progress.update(_zsuite_switch_t0_start_sequence())
                no_progress.update(_zsuite_single_tail_sequence(prof))
            else:
                no_progress.update(_zsuite_switch_t1_start_sequence())
                no_progress.update(ZS_T1_FAST_CLEAN_PASS_SEQUENCE)
                no_progress.update(_zsuite_dual_tail_sequence())
        for _src, raw in list(ZSUITE_START_SINGLE_E_PROFILES.values()) + [ZSUITE_START_SINGLE_E_FALLBACK]:
            vals = tuple(Decimal(x) for x in raw)
            no_progress.update([_feedrate_cmd(4800), _e_move_cmd(0xFE, vals[0]), _feedrate_cmd(2100), _e_move_cmd(0xFE, vals[1]), _e_move_cmd(0xFD, vals[2]), _restore_e_zero_cmd()])
        for _src, raw in list(ZSUITE_START_DUAL_E_PROFILES.values()) + list(ZSUITE_START_DUAL_MODEL_FALLBACKS.values()) + [ZSUITE_START_DUAL_E_FALLBACK]:
            vals = tuple(Decimal(x) for x in raw)
            no_progress.update([_feedrate_cmd(480), _e_move_cmd(0xEA, vals[0]), _feedrate_cmd(3600), _e_move_cmd(0xFE, vals[1]), zcmd_simple(12, pack_i32(3000)), _feedrate_cmd(3600), _e_move_cmd(0xFD, vals[2]), _restore_e_zero_cmd()])
        for seq in ZS_END_MACHINE_SEQUENCES.values():
            no_progress.update(seq)
        for seq in ZS_CLEAN_MACHINE_SEQUENCES.values():
            no_progress.update(seq)
        for seq in (ZS_POST_CLEAN_RESTORE_SINGLE, ZS_POST_CLEAN_RESTORE_DUAL):
            no_progress.update(seq)
        # Keep explicitly requested special-position cleaning sequences contiguous too.
        for code in set(SPECIAL_POSITION_CODES.values()):
            no_progress.add(zcmd_special_position(code))
    except Exception:
        pass
    return no_progress

def append_report_progress(commands: list[bytes]) -> list[bytes]:
    out: list[bytes] = []
    size = len(commands)
    step = max(1, math.ceil(size / 100))
    p = 0
    no_progress = _no_progress_inside_command_set()
    for i, cmd in enumerate(commands):
        if cmd not in no_progress and i % step == 0 and p <= 100:
            out.append(zcmd_simple(11, p))
            p += 1
        out.append(cmd)
    if p == 100:
        out.append(zcmd_simple(11, 100))
    end_cmd = zcmd_simple(19)
    if end_cmd not in out:
        out.append(end_cmd)
    return out


def _next_tool_command(lines: list[str], start_index: int, lookahead: int = 250) -> int | None:
    """Return the next T0/T1 command shortly after a clean marker.

    Orca 2.3.2 can emit Change filament G-code before the actual T0/T1 line.
    In that case AUTO/DUAL cleaning must apply to the upcoming tool, not to the
    currently active one. The lookahead is intentionally large because Orca can
    place temperature/wait commands between the marker and the actual T command.
    """
    end = min(len(lines), start_index + lookahead)
    for j in range(start_index, end):
        cmd, _comment, _params = parse_line(lines[j])
        if cmd in ("T0", "T1"):
            return int(cmd[1:])
        # Do not stop on M/G housekeeping here: Orca may insert waits and moves
        # around toolchange. A following T0/T1 still tells us the intended tool.
    return None

def _mark_tools_cleaned_after_start(st: AxisState, mode: str, single_material: bool | None) -> None:
    mode_token, _speed_opts = _parse_marker_mode_and_options(mode)
    key = _machine_mode_key(mode_token, single_material)
    if key == "SINGLE":
        st.cleaned_tools.add(0)
        st.active_extruder = 0
    else:
        # Observed behavior in the current same-STL dual test: the Z-Suite-like
        # start sequence ends with/supports T1 prepared. T0 must still be cleaned
        # at its first real use.
        st.cleaned_tools.add(1)
        st.active_extruder = 1

# ---------------------------------------------------------------------------
# Z-Suite-like SPECIAL_CLEAN / toolchange cleaning
# ---------------------------------------------------------------------------

ZSUITE_IDLE_RETRACT_AUTO_MM = Decimal("20.00")
ZSUITE_IDLE_RETRACT_AUTO_F = 480
# Confirmed native Z-Suite dual T0 clean profile after physical test.
ZSUITE_DUAL_T0_CLEAN_E_MOVES = (Decimal("21.000"), Decimal("22.000"), Decimal("21.000"))
ZSUITE_DUAL_T0_CLEAN_FEEDS = (480, 2000, 2000)


def _clean_path_for_tool(tool: int) -> list[bytes]:
    """Return the confirmed Z-Suite clean path for active T0/T1.

    T1 path from original dual starts/toolchanges:
        09 -> 07 -> 0A -> 08 -> 09 -> 07 -> 00
    T0 path from original dual toolchanges:
        0A -> 08 -> 09 -> 07 -> 0A -> 08 -> 00
    Both are emitted at F7200 in the fast-clean form observed in Z-Suite.
    """
    seq = [0x09, 0x07, 0x0A, 0x08, 0x09, 0x07, 0x00] if int(tool) == 1 else [0x0A, 0x08, 0x09, 0x07, 0x0A, 0x08, 0x00]
    out: list[bytes] = []
    for code in seq:
        out.append(_feedrate_cmd(7200))
        out.append(zcmd_special_position(code))
    return out


def _toolchange_switch_path_zsuite(target_tool: int, old_tool: int | None, retract_mm: Decimal | None, retract_f: int | None, speed_opts: dict[str, object] | None = None, meta: GCodeMetadata | None = None) -> list[bytes]:
    """Emit the Z-Suite-like switch path to target tool.

    This includes the observed old-head retract between the parking/start
    position and the final slow switch position.  The exact E command extra byte
    differs for old T0 vs old T1 in Z-Suite references:
      old T0 retract: 08 01 E9 ... -20 mm
      old T1 retract: 08 01 F3 ... -20 mm
    """
    target_tool = int(target_tool)
    out: list[bytes] = []
    if target_tool == 1:
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x06)])
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x09)])
        if retract_mm is not None and retract_mm > 0:
            extra = 0xE9 if int(old_tool or 0) == 0 else 0xF3
            out.extend([_feedrate_cmd(_scaled_feedrate(int(retract_f or ZSUITE_IDLE_RETRACT_AUTO_F), _speed_scale_from_opts(speed_opts, "retract_speed_scale", meta=meta, tool=old_tool if old_tool is not None else target_tool, mode="TOOLCHANGE_RETRACT"))), _e_move_cmd(extra, -Decimal(retract_mm)), _restore_e_zero_cmd()])
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x04)])
        out.extend([_feedrate_cmd(250), zcmd_special_position(0x02)])
        out.append(zcmd_simple(7, 1))
    else:
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x05)])
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x0A)])
        if retract_mm is not None and retract_mm > 0:
            extra = 0xF3 if int(old_tool or 1) == 1 else 0xE9
            out.extend([_feedrate_cmd(_scaled_feedrate(int(retract_f or ZSUITE_IDLE_RETRACT_AUTO_F), _speed_scale_from_opts(speed_opts, "retract_speed_scale", meta=meta, tool=old_tool if old_tool is not None else target_tool, mode="TOOLCHANGE_RETRACT"))), _e_move_cmd(extra, -Decimal(retract_mm)), _restore_e_zero_cmd()])
        out.extend([_feedrate_cmd(7200), zcmd_special_position(0x03)])
        out.extend([_feedrate_cmd(250), zcmd_special_position(0x01)])
        out.append(zcmd_simple(7, 0))
    return out


def _resolve_special_clean_retract(value: Decimal | None) -> Decimal | None:
    if value == Decimal("-1"):
        return ZSUITE_IDLE_RETRACT_AUTO_MM
    return value


def _resolve_special_clean_retract_f(value: int | None) -> int:
    return int(value or ZSUITE_IDLE_RETRACT_AUTO_F)


def _special_clean_profile_for_tool(tool: int, meta: GCodeMetadata, purge_mm: Decimal | None) -> tuple[str, tuple[Decimal, Decimal, Decimal]] | None:
    """Choose E1/E2/E3 purge-prime values for SPECIAL_CLEAN.

    PURGE=AUTO maps to the material/profile based Z-Suite values already used
    by START_MACHINE.  Numeric PURGE=<mm> is treated as a manual override and
    applied to all three E moves.  Absence of PURGE disables E moves and emits
    only the movement/clean path.
    """
    if purge_mm is None:
        return None
    if purge_mm == Decimal("-1"):
        # Use confirmed Z-Suite dual clean profiles. T0 must not reuse the
        # single-start purge profile; that caused excessive prime/load behavior
        # and possible filament-runout/load procedure symptoms.
        if int(tool) == 1:
            source, moves = _choose_zsuite_start_e_profile("DUAL", meta)
            return f"SPECIAL_CLEAN AUTO from DUAL/T1 start profile: {source}", moves
        return "SPECIAL_CLEAN AUTO from confirmed native Z-Suite dual T0 clean profile", ZSUITE_DUAL_T0_CLEAN_E_MOVES
    if purge_mm > 0:
        return f"SPECIAL_CLEAN manual PURGE={purge_mm} mm", (Decimal(purge_mm), Decimal(purge_mm), Decimal(purge_mm))
    return None



def _single_material_t0_clean_body(meta: GCodeMetadata, speed_opts: dict[str, object] | None = None) -> tuple[list[bytes], str, tuple[Decimal, Decimal, Decimal]]:
    """LAB38-safe SINGLE/T0 clean body.

    Single LAB38 is the protected reference path.  It must not use the dual
    T1->T0 clean profile (area F4 + dwell), because that changes the confirmed
    single stream.  In single mode T0 cleaning stays Z-Suite-like single style:
    POS00 -> FE/FE purge -> T0 brush path -> FD restore, no dwell.
    """
    source, moves = _choose_zsuite_start_e_profile("SINGLE", meta)
    feeds = (4800, 2100, 2100)
    model_for_feed = _canonical_material_for_tool(meta, 0)
    if model_for_feed and model_for_feed in ZSUITE_START_SINGLE_E_FEED_PROFILES:
        source, raw_moves, feeds = ZSUITE_START_SINGLE_E_FEED_PROFILES[model_for_feed]
        moves = tuple(Decimal(x) for x in raw_moves)  # type: ignore[assignment]
    e_scale = _speed_scale_from_opts(speed_opts, "e_speed_scale", meta=meta, tool=0, mode="SINGLE_T0_CLEAN")
    f0 = _scaled_feedrate(feeds[0], e_scale)
    f1 = _scaled_feedrate(feeds[1], e_scale)
    f2 = _scaled_feedrate(feeds[2], e_scale)
    out: list[bytes] = [
        _feedrate_cmd(f0),
        _e_move_cmd(0xFE, moves[0]),
        _feedrate_cmd(f1),
        _e_move_cmd(0xFE, moves[1]),
    ]
    if f2 != f1:
        out.append(_feedrate_cmd(f2))
    out.extend(_clean_path_for_tool(0))
    out.extend([
        _e_move_cmd(0xFD, moves[2]),
        _restore_e_zero_cmd(),
    ])
    return out, source, moves

def _emit_zsuite_clean_body_for_tool(st: AxisState, tool: int, meta: GCodeMetadata, purge_mm: Decimal | None, purge_f: int | None, speed_opts: dict[str, object] | None = None) -> list[bytes]:
    """Emit center -> E1/E2 -> fast clean path -> E3/restore for active tool."""
    out: list[bytes] = [_feedrate_cmd(7200), zcmd_special_position(0x00)]
    chosen = _special_clean_profile_for_tool(tool, meta, purge_mm)
    if chosen is not None:
        source, moves = chosen
        e_scale = _speed_scale_from_opts(speed_opts, "e_speed_scale", meta=meta, tool=tool, mode="CLEAN_BODY")
        if int(tool) == 1:
            # Reference DUAL/T1 start and toolchange: F480/E1, F3600/E2, dwell, clean, F3600/E3.
            out.extend([_feedrate_cmd(_scaled_feedrate(int(purge_f or 480), e_scale)), _e_move_cmd(0xEA, moves[0])])
            out.extend([_feedrate_cmd(_scaled_feedrate(3600, e_scale)), _e_move_cmd(0xFE, moves[1])])
            out.append(zcmd_simple(12, pack_i32(3000)))
            out.extend(_clean_path_for_tool(tool))
            out.extend([_feedrate_cmd(_scaled_feedrate(3600, e_scale)), _e_move_cmd(0xFD, moves[2]), _restore_e_zero_cmd()])
        else:
            if bool(meta.single_material):
                # Protected LAB38/SINGLE path.  Do not use dual T0 F4+dwell
                # clean in single-material jobs.
                single_body, single_source, single_moves = _single_material_t0_clean_body(meta, speed_opts)
                out.extend(single_body)
                source, moves = single_source, single_moves
            else:
                # Confirmed native Z-Suite DUAL/T0 clean body:
                # F480 E+21 area F4 -> F2000 E+22 area FE -> DWELL 3000 ->
                # T0 brush path 0A 08 09 07 0A 08 00 -> F2000 E+21 area FD -> RESTORE E0.
                # This is used by TOOLCHANGE_CLEAN T1->T0 and by LAYER_CLEAN
                # when T0 is the active tool in dual mode. START_MACHINE SINGLE
                # and single-material LAYER_CLEAN remain separate.
                out.extend([_feedrate_cmd(_scaled_feedrate(int(purge_f or ZSUITE_DUAL_T0_CLEAN_FEEDS[0]), e_scale)), _e_move_cmd(0xF4, moves[0])])
                out.extend([_feedrate_cmd(_scaled_feedrate(ZSUITE_DUAL_T0_CLEAN_FEEDS[1], e_scale)), _e_move_cmd(0xFE, moves[1])])
                out.append(zcmd_simple(12, pack_i32(3000)))
                out.extend(_clean_path_for_tool(tool))
                out.extend([_feedrate_cmd(_scaled_feedrate(ZSUITE_DUAL_T0_CLEAN_FEEDS[2], e_scale)), _e_move_cmd(0xFD, moves[2]), _restore_e_zero_cmd()])
        diagnostic_print(f"[special-clean-profile] T{int(tool)} {source}: E moves {moves[0]} / {moves[1]} / {moves[2]} mm")
    else:
        out.extend(_clean_path_for_tool(tool))
    return out


def _emit_zsuite_toolchange_clean(
    st: AxisState,
    target_tool: int,
    old_tool: int | None,
    meta: GCodeMetadata,
    purge_mm: Decimal | None,
    purge_f: int | None,
    idle_retract_mm: Decimal | None,
    idle_retract_f: int | None,
    clean_opts: dict[str, object] | None = None,
) -> list[bytes]:
    """Emit Z-Suite-like complete toolchange + clean for Change filament G-code."""
    target_tool = int(target_tool)
    pending_new_temp = _pending_tool_temp(st, "new_temp")
    retract = _resolve_special_clean_retract(idle_retract_mm)
    retract_f = _resolve_special_clean_retract_f(idle_retract_f)
    out: list[bytes] = []
    # Restore Orca ooze-prevention/preheat intent: set the incoming tool to
    # print temperature as early as possible in the marker, then continue the
    # mechanical switch. A later wait immediately before purge guarantees temp.
    out.extend(_emit_toolchange_preheat(meta, target_tool, clean_opts, pending_temp=pending_new_temp))
    out.extend(_toolchange_switch_path_zsuite(target_tool, old_tool, retract, retract_f, clean_opts, meta))
    # After the old tool has been retracted, cool it to standby/idle temperature
    # so it does not ooze over the model while inactive.
    out.extend(_emit_inactive_tool_standby(meta, old_tool, clean_opts))
    st.active_extruder = target_tool
    # Before purge/prime of the newly selected tool, force actual Orca material
    # temperature and wait.
    out.extend(_emit_clean_tool_temp(meta, target_tool, clean_opts, initial=False, pending_temp=pending_new_temp, wait=True))
    out.extend(_emit_zsuite_clean_body_for_tool(st, target_tool, meta, purge_mm, purge_f, clean_opts))
    out.extend(zcmd_post_clean_restore_sequence("T1" if target_tool == 1 else "T0", meta))
    st.pending_post_clean_min_feedrate = post_clean_min_feedrate("T1" if target_tool == 1 else "T0", meta)
    st.cleaned_tools.add(target_tool)
    return out


def _emit_zsuite_layer_clean(
    st: AxisState,
    tool: int,
    meta: GCodeMetadata,
    purge_mm: Decimal | None,
    purge_f: int | None,
    idle_retract_mm: Decimal | None = None,
    idle_retract_f: int | None = None,
    clean_opts: dict[str, object] | None = None,
) -> list[bytes]:
    """Emit periodic layer clean for the active/current tool.

    This is intended for ;ZORTRAX_LAYER_CLEAN in Layer change G-code.
    It intentionally does not run the full Z-Suite switch path.  If an explicit
    T0/T1 layer-clean is requested, the caller may select that tool before this
    function is called.  Optional IDLE_RETRACT is treated as a pre-clean retract
    of the currently active tool; AUTO uses the confirmed Z-Suite -20 mm @ F480.
    """
    tool = int(tool)
    out: list[bytes] = []
    retract = _resolve_special_clean_retract(idle_retract_mm)
    if retract is not None and retract > 0:
        extra = 0xF3 if tool == 1 else 0xE9
        out.extend([_feedrate_cmd(_scaled_feedrate(_resolve_special_clean_retract_f(idle_retract_f), _speed_scale_from_opts(clean_opts, "retract_speed_scale", meta=meta, tool=tool, mode="LAYER_CLEAN_RETRACT"))), _e_move_cmd(extra, -Decimal(retract)), _restore_e_zero_cmd()])
    # Layer-clean happens during printing, but force the active material
    # temperature before any purge/prime move. This is important after long
    # idle periods or user-defined temperature management.
    out.extend(_emit_clean_tool_temp(meta, tool, clean_opts, initial=False, wait=True))
    out.extend(_emit_zsuite_clean_body_for_tool(st, tool, meta, purge_mm, purge_f, clean_opts))
    out.extend(zcmd_post_clean_restore_sequence("T1" if tool == 1 else "T0", meta))
    st.pending_post_clean_min_feedrate = post_clean_min_feedrate("T1" if tool == 1 else "T0", meta)
    st.cleaned_tools.add(tool)
    return out


_ZORTRAX_T0_KEYS = {"T0", "MODEL", "0", "TOOL0", "EXTRUDER0"}
_ZORTRAX_T1_KEYS = {"T1", "SUPPORT", "1", "TOOL1", "EXTRUDER1"}
_ZORTRAX_AUTO_KEYS = {"AUTO", "CURRENT", "CURRENT_TOOL", ""}
_ZORTRAX_DUAL_KEYS = {"DUAL", "FULL_DUAL", "DUAL_FULL", "BOTH"}


def _marker_mode_explicit_tool(mode: str) -> int | None:
    key = _normalize_marker_token(mode or "AUTO")
    if key in _ZORTRAX_T0_KEYS:
        return 0
    if key in _ZORTRAX_T1_KEYS:
        return 1
    return None


def _emit_marker_toolchange_clean(
    st: AxisState,
    mode: str,
    meta: GCodeMetadata,
    lines: list[str],
    idx: int,
    purge_mm: Decimal | None,
    purge_f: int | None,
    idle_retract_mm: Decimal | None,
    idle_retract_f: int | None,
    clean_opts: dict[str, object] | None = None,
) -> list[bytes]:
    """Handler for ;ZORTRAX_TOOLCHANGE_CLEAN.

    Intended for Orca Change filament G-code.  It mirrors the original Z-Suite
    dual toolchange structure:
      switch path with old-head retract -> select target tool -> center ->
      material/profile based E moves -> fast clean path -> post-clean E/restore.
    No layer interval is applied here; this marker runs at each real toolchange.
    """
    key = _normalize_marker_token(mode or "AUTO")
    next_tool = _tool_from_meta_value(st.pending_toolchange_meta.get("next_extruder"))
    previous_tool = _tool_from_meta_value(st.pending_toolchange_meta.get("previous_extruder"))
    if previous_tool is None:
        previous_tool = st.active_extruder
    if next_tool is None:
        next_tool = _next_tool_command(lines, idx)

    # Best effort: do not perform a full toolchange-clean if Orca reports no
    # actual tool change.  This also avoids setting the layer-clean skip flag
    # for metadata-only blocks.
    no_real_toolchange = (previous_tool is not None and next_tool is not None and int(previous_tool) == int(next_tool))

    explicit_tool = _marker_mode_explicit_tool(mode)
    if explicit_tool is not None:
        target_tool = explicit_tool
    elif key in _ZORTRAX_AUTO_KEYS:
        target_tool = next_tool if next_tool is not None else st.active_extruder
    else:
        raise ValueError(f"Unknown ZORTRAX_TOOLCHANGE_CLEAN mode: {mode!r}")

    if no_real_toolchange and explicit_tool is None:
        diagnostic_print(
            f"[toolchange-clean] skipped: previous_extruder={previous_tool} next_extruder={next_tool} on layer {st.current_layer}"
        )
        return []

    out = _emit_zsuite_toolchange_clean(
        st,
        int(target_tool),
        previous_tool,
        meta,
        purge_mm,
        purge_f,
        idle_retract_mm,
        idle_retract_f,
        clean_opts,
    )
    if out:
        st.last_toolchange_clean_layer = int(st.current_layer)
        st.toolchange_clean_skip_pending = True
        st.skip_next_post_toolchange_m109_tool = int(target_tool)
    return out



def _future_tool_use(lines: list[str], idx: int, tool: int) -> bool:
    """Return True if G-code after current marker contains a real future use of tool.

    This intentionally checks only executable/real marker lines, not the settings
    dump comments at the end of Orca files.  Used to prevent periodic DUAL layer
    clean from switching to an inactive support head after the last support/tower
    use has already finished.
    """
    tool = int(tool)
    t_cmd = f"T{tool}"
    for raw in lines[idx + 1:]:
        s = raw.strip()
        if not s:
            continue
        if s.startswith(';ZORTRAX_TOOLCHANGE_META'):
            kv = _parse_marker_key_values(s[len(';ZORTRAX_TOOLCHANGE_META'):].strip())
            nt = _tool_from_meta_value(kv.get('next_extruder'))
            if nt is not None and int(nt) == tool:
                return True
            continue
        # Real Orca tool command. Do not match '; change_filament_gcode = ... T1 ...'
        if s.startswith(t_cmd) and (len(s) == 2 or s[2].isspace() or s[2] == ';'):
            return True
    return False


def _dual_layer_clean_tool_list(st: AxisState, key: str, lines: list[str] | None, idx: int | None) -> list[int]:
    """Tool list for ;ZORTRAX_LAYER_CLEAN DUAL.

    DUAL is now smart: always clean/restore the active/current tool, but only
    clean the inactive tool if that tool will still be used later in the file.
    FULL_DUAL / DUAL_FULL / BOTH retain forced both-head behavior.
    """
    active = st.active_extruder if st.active_extruder in (0, 1) else 0
    key = _normalize_marker_token(key or 'AUTO')
    if key in {'FULL_DUAL', 'DUAL_FULL', 'BOTH'}:
        return [0, 1]
    other = 1 - int(active)
    tools = [int(active)]
    if lines is not None and idx is not None and _future_tool_use(lines, idx, other):
        tools.append(other)
    return tools

def _emit_marker_layer_clean(
    st: AxisState,
    mode: str,
    clean_interval: int | None,
    meta: GCodeMetadata,
    purge_mm: Decimal | None,
    purge_f: int | None,
    idle_retract_mm: Decimal | None = None,
    idle_retract_f: int | None = None,
    clean_opts: dict[str, object] | None = None,
    lines: list[str] | None = None,
    idx: int | None = None,
) -> list[bytes]:
    """Handler for ;ZORTRAX_LAYER_CLEAN.

    Intended for Orca Layer change G-code.  It can be gated with EVERY=N and
    reuses the same center/purge/profile/clean subprocedures as toolchange clean,
    but it does not run the Z-Suite old-tool switch path.
    """
    if not _clean_allowed_on_current_layer(st, clean_interval, clean_opts):
        return []

    key = _normalize_marker_token(mode or "AUTO")
    out: list[bytes] = []
    if key in _ZORTRAX_DUAL_KEYS:
        # Periodic maintenance mode.  v1.4.15/v1.2.20 safety fix:
        # clean both heads only while both will still be used later; otherwise
        # do not switch to an already-finished support head on the final model/tower layers.
        # Always restore the originally active tool before returning to normal G-code.
        original_tool = st.active_extruder if st.active_extruder in (0, 1) else 0
        tools_to_clean = _dual_layer_clean_tool_list(st, key, lines, idx)
        diagnostic_print(f"[layer-clean] DUAL smart tools={tools_to_clean}; restore T{original_tool}; layer={st.current_layer}")
        for tool in tools_to_clean:
            if st.active_extruder != tool:
                out.append(zcmd_simple(7, tool))
                st.active_extruder = tool
            out.extend(_emit_zsuite_layer_clean(st, tool, meta, purge_mm, purge_f, idle_retract_mm, idle_retract_f, clean_opts))
        if st.active_extruder != original_tool:
            out.append(zcmd_simple(7, int(original_tool)))
            st.active_extruder = int(original_tool)
            out.extend(_emit_clean_tool_temp(meta, int(original_tool), clean_opts, initial=False, wait=True))
        return out

    explicit_tool = _marker_mode_explicit_tool(mode)
    if explicit_tool is not None:
        if st.active_extruder != explicit_tool:
            out.append(zcmd_simple(7, explicit_tool))
            st.active_extruder = explicit_tool
        target_tool = explicit_tool
    elif key in _ZORTRAX_AUTO_KEYS:
        target_tool = st.active_extruder
    else:
        raise ValueError(f"Unknown ZORTRAX_LAYER_CLEAN mode: {mode!r}")

    out.extend(_emit_zsuite_layer_clean(st, int(target_tool), meta, purge_mm, purge_f, idle_retract_mm, idle_retract_f, clean_opts))
    return out


def _emit_first_use_clean_for_tool(st: AxisState, tool: int, meta: GCodeMetadata, force: bool = False, purge_mm: Decimal | None = None, purge_f: int | None = None) -> list[bytes]:
    if not force and tool in st.cleaned_tools:
        return []
    # Backward-compatible path: treat first-use as layer/current clean for the target tool.
    st.active_extruder = int(tool)
    return _emit_zsuite_layer_clean(st, int(tool), meta, purge_mm, purge_f, None, None, None)


def _parse_clean_marker_args(arg_text: str) -> tuple[str, int | None, Decimal | None, int | None, Decimal | None, int | None]:
    """Parse clean-marker arguments for ;ZORTRAX_TOOLCHANGE_CLEAN, ;ZORTRAX_LAYER_CLEAN, and legacy ;ZORTRAX_SPECIAL_CLEAN.

    Examples:
      ;ZORTRAX_TOOLCHANGE_CLEAN AUTO PURGE=AUTO IDLE_RETRACT=AUTO
      ;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 PURGE=AUTO
      ;ZORTRAX_LAYER_CLEAN T0 10 PURGE=8 IDLE_RETRACT=20
      ;ZORTRAX_SPECIAL_CLEAN AUTO 10 PURGE=8  # legacy compatibility

    The optional numeric interval keeps the v11 behavior. PURGE without a value
    uses a conservative default of 8 mm. PURGE_F is in mm/min, like normal G-code F.
    If PURGE_F is omitted, v1.06 automatically uses deretraction_speed[active_tool] from
    ORCA METADATA, converted from mm/s to mm/min.
    IDLE_RETRACT retracts the tool that becomes inactive; when that tool is activated later,
    the same amount is unretracted before clean/purge. If IDLE_RETRACT_F is omitted,
    v1.06 uses retraction_speed[inactive_tool] for retract and deretraction_speed[active_tool]
    for unretract, again converted from mm/s to mm/min.
    """
    text = (arg_text or "").strip()
    if not text:
        return "AUTO", None, None, None, None, None
    parts = text.split()
    mode = parts[0]
    interval = None
    purge_mm: Decimal | None = None
    purge_f: int | None = None
    idle_retract_mm: Decimal | None = None
    idle_retract_f: int | None = None
    for token in parts[1:]:
        t = token.strip().strip(",;")
        m = re.match(r"(?i)^(?:EVERY|CO|INTERVAL|LAYER_INTERVAL)\s*=\s*(\d+)$", t)
        if m:
            interval = int(m.group(1))
            continue
        m = re.match(r"(?i)^PURGE(?:_MM)?\s*=\s*([-+]?\d*\.?\d+)$", t)
        if m:
            purge_mm = Decimal(m.group(1))
            continue
        if re.match(r"(?i)^PURGE(?:_MM)?\s*=\s*AUTO$", t):
            purge_mm = Decimal("-1")
            continue
        if re.match(r"(?i)^PURGE$", t):
            purge_mm = Decimal("8")
            continue
        m = re.match(r"(?i)^(?:PURGE_F|PURGE_FEEDRATE|PURGE_SPEED)\s*=\s*(\d+)$", t)
        if m:
            purge_f = int(m.group(1))
            continue
        m = re.match(r"(?i)^(?:IDLE_RETRACT|IDLE_RETRACT_MM|IDLE_RETRACTION)\s*=\s*([-+]?\d*\.?\d+)$", t)
        if m:
            idle_retract_mm = Decimal(m.group(1))
            continue
        if re.match(r"(?i)^(?:IDLE_RETRACT|IDLE_RETRACT_MM|IDLE_RETRACTION)\s*=\s*AUTO$", t):
            idle_retract_mm = Decimal("-1")
            continue
        if re.match(r"(?i)^IDLE_RETRACT$", t):
            idle_retract_mm = Decimal("3")
            continue
        m = re.match(r"(?i)^(?:IDLE_RETRACT_F|IDLE_RETRACT_FEEDRATE|IDLE_RETRACT_SPEED)\s*=\s*(\d+)$", t)
        if m:
            idle_retract_f = int(m.group(1))
            continue
        elif re.fullmatch(r"\d+", t):
            interval = int(t)
    if interval is not None and interval <= 1:
        interval = None
    if purge_mm is not None and purge_mm == Decimal("-1"):
        pass
    elif purge_mm is not None and purge_mm <= 0:
        purge_mm = None
    if idle_retract_mm is not None and idle_retract_mm == Decimal("-1"):
        pass
    elif idle_retract_mm is not None and idle_retract_mm <= 0:
        idle_retract_mm = None
    return mode, interval, purge_mm, purge_f, idle_retract_mm, idle_retract_f

def zcmd_purge_sequence(st: AxisState, purge_mm: Decimal | None, purge_f: int | None) -> list[bytes]:
    """Emit an optional E-only purge without changing X/Y/Z.

    The sequence uses temporary relative-E motion and then restores the currently
    expected E coordinate with G92-style command. This keeps Orca's later E values
    consistent while physically extruding purge material in the cleaning area.
    """
    if purge_mm is None or purge_mm <= 0:
        return []
    feed = int(purge_f or 360)
    current_e = st.current.get("E", Decimal(0))
    out = [
        zcmd_simple(2, pack_i32(feed)),
        zcmd_axis(10, {"E": Decimal(0)}),
        zcmd_axis_with_values(1, {"E": purge_mm}, UNKNOWN_PRINTING_AREA),
        zcmd_axis_with_values(4, {"E": current_e}),
    ]
    if not st.relative_e:
        out.append(zcmd_axis(9, {"E": Decimal(0)}))
    return out


def zcmd_idle_e_delta_sequence(st: AxisState, delta_mm: Decimal, feedrate: int | None) -> list[bytes]:
    """Physically move E by delta_mm, then restore the logical E coordinate.

    Used for inactive-tool retract / active-tool unretract around real T0/T1 changes.
    This is deliberately separate from PURGE: idle retract compensates ooze pressure,
    while PURGE intentionally extrudes extra material into the cleaning area.
    """
    if delta_mm == 0:
        return []
    feed = int(feedrate or 900)
    current_e = st.current.get("E", Decimal(0))
    out = [
        zcmd_simple(2, pack_i32(feed)),
        zcmd_axis(10, {"E": Decimal(0)}),
        zcmd_axis_with_values(1, {"E": delta_mm}, UNKNOWN_PRINTING_AREA),
        zcmd_axis_with_values(4, {"E": current_e}),
    ]
    if not st.relative_e:
        out.append(zcmd_axis(9, {"E": Decimal(0)}))
    return out


def zcmd_idle_retract_before_toolchange(st: AxisState, old_tool: int, amount_mm: Decimal | None, feedrate: int | None) -> list[bytes]:
    if amount_mm is None or amount_mm <= 0:
        return []
    old_amount = st.idle_retracted_mm.get(old_tool, Decimal(0))
    if old_amount > 0:
        return []
    st.idle_retracted_mm[old_tool] = amount_mm
    return zcmd_idle_e_delta_sequence(st, -amount_mm, feedrate)


def zcmd_idle_unretract_after_toolchange(st: AxisState, new_tool: int, feedrate: int | None) -> list[bytes]:
    amount = st.idle_retracted_mm.get(new_tool, Decimal(0))
    if amount <= 0:
        return []
    st.idle_retracted_mm[new_tool] = Decimal(0)
    return zcmd_idle_e_delta_sequence(st, amount, feedrate)


def _clean_allowed_on_current_layer(st: AxisState, interval: int | None, clean_opts: dict[str, object] | None = None) -> bool:
    """Return whether LAYER_CLEAN should run on the current layer.

    START_LAYER=2 / MIN_LAYER=2 prevents clean on the first printed layer.
    With EVERY=N and START_LAYER=2, cleaning runs on layers 2, 2+N, 2+2N...
    SKIP_FIRST=1 is an alias for START_LAYER=2.
    If no START_LAYER/SKIP_FIRST is provided, legacy v1.2.4 behavior is preserved.
    """
    opts = clean_opts or {}
    start_layer = opts.get("start_layer")
    try:
        start_layer_i = int(start_layer) if start_layer is not None else None
    except Exception:
        start_layer_i = None
    if opts.get("skip_first") and start_layer_i is None:
        start_layer_i = 2

    if start_layer_i is not None:
        if st.current_layer <= 0:
            return False
        if st.current_layer < start_layer_i:
            return False

    if interval is None:
        layer_allowed = True
    elif st.current_layer <= 0:
        layer_allowed = start_layer_i is None
    elif start_layer_i is not None:
        layer_allowed = ((st.current_layer - start_layer_i) % interval) == 0
    else:
        layer_allowed = (st.current_layer % interval) == 0

    if not layer_allowed:
        return False

    if opts.get("skip_after_toolchange"):
        last_tc = st.last_toolchange_clean_layer
        if st.current_layer <= 0 and st.toolchange_clean_skip_pending:
            st.toolchange_clean_skip_pending = False
            diagnostic_print("[layer-clean] skipped after TOOLCHANGE_CLEAN because current layer is unknown/0")
            return False
        if st.toolchange_clean_skip_pending and last_tc is not None and st.current_layer > 0:
            # Orca may place Layer change G-code on the same logical layer as
            # the toolchange or on the immediately following printed layer.
            # Skip only the first eligible layer-clean after the toolchange;
            # do not suppress later periodic clean operations.
            if st.current_layer == last_tc or st.current_layer == last_tc + 1:
                st.toolchange_clean_skip_pending = False
                diagnostic_print(f"[layer-clean] skipped after TOOLCHANGE_CLEAN on layer {st.current_layer}")
                return False
        if st.current_layer > 0 and last_tc is not None and st.current_layer > last_tc + 1:
            st.toolchange_clean_skip_pending = False

    return True



def _lab05_area_from_orca_type(type_text: str, layer_index: int) -> int:
    """Map Orca verbose ;TYPE comments to ZTool/Z-Suite PrintingArea values."""
    t = (type_text or "").strip().lower().replace("_", " ").replace("-", " ")
    first = layer_index == 0
    if not t:
        return UNKNOWN_PRINTING_AREA
    if "travel" in t or "jump" in t:
        return UNKNOWN_PRINTING_AREA
    if "skirt" in t or "brim" in t:
        return AREA_SUPPORT_INFILL
    if "support interface" in t:
        return AREA_SUPPORT_INTERFACE_INFILL
    if "support" in t:
        return AREA_SUPPORT_INFILL
    if "bridge" in t:
        return AREA_BRIDGE_INFILL
    if "outer wall" in t or "external perimeter" in t or "external wall" in t:
        return AREA_FIRST_LAYER_MODEL_CONTOUR if first else AREA_MODEL_CONTOUR
    if "inner wall" in t or "internal wall" in t or "perimeter" in t or "wall" in t:
        return AREA_FIRST_LAYER_MODEL_CONTOUR if first else AREA_MODEL_INVISIBLE_CONTOUR
    if "top surface" in t or "top solid" in t:
        return AREA_VISIBLE_TOP_INFILL
    if "bottom surface" in t or "bottom solid" in t:
        return AREA_FIRST_LAYER_MODEL_FILL if first else AREA_VISIBLE_BOTTOM_INFILL
    if "internal solid" in t or "solid infill" in t:
        return AREA_FIRST_LAYER_MODEL_FILL if first else AREA_INVISIBLE_INFILL
    if "sparse infill" in t or "infill" in t or "gap fill" in t:
        return AREA_FIRST_LAYER_MODEL_FILL if first else AREA_INVISIBLE_INFILL
    if "prime tower" in t or "wipe tower" in t or "waste tower" in t:
        return AREA_WASTE_TOWER_MODEL
    return UNKNOWN_PRINTING_AREA

def _update_layer_state_from_comment(st: AxisState, marker: str) -> None:
    txt = marker.strip()
    up = txt.upper()
    if up.startswith("LAYER_CHANGE"):
        st.current_layer += 1
        st.zsuite_layer_index += 1
        st.current_orca_type = ""
        st.current_area = UNKNOWN_PRINTING_AREA
        return
    if up.startswith("TYPE:"):
        st.current_orca_type = txt.split(":", 1)[1].strip()
        st.current_area = _lab05_area_from_orca_type(st.current_orca_type, max(st.zsuite_layer_index, 0))
        return
    m = re.match(r"(?i)^layer\s*#\s*(\d+)", txt)
    if m:
        try:
            st.current_layer = int(m.group(1))
            st.zsuite_layer_index = st.current_layer
        except Exception:
            pass



def _area_is_top_like(area: int) -> bool:
    return area in {
        AREA_VISIBLE_TOP_INFILL,
        AREA_MODEL_CONTOUR,
        AREA_MODEL_INVISIBLE_CONTOUR,
        AREA_MODEL_CONTOUR_ENTRANCE,
        AREA_MODEL_CONTOUR_EXIT,
    }


def _lab14_motion_area(base_area: int, has_xy: bool, dxy: Decimal, has_e: bool, de: Decimal) -> int:
    """Return Z-Suite viewer area/path after LAB14 connector semantics.

    Physical movement payload is unchanged. Only the PrintingArea byte is
    adjusted so Z-Suite does not render non-print connector/travel moves as
    model/support/raft/waste geometry.

    Rule order:
    1. pure E -> retraction/deretraction class;
    2. XY with no positive E -> JUMP_PATH;
    3. long XY with very small E/mm -> JUMP_PATH;
    4. short top low-E -> SEAM;
    5. otherwise keep current Orca/Z-Suite area mapping.
    """
    if not has_xy and has_e:
        if de < 0:
            return AREA_RETRACTION_BACK
        if de > 0:
            return AREA_RETRACTION_FORWARD
        return AREA_JUMP_PATH

    if has_xy and (not has_e or de <= 0):
        return AREA_JUMP_PATH

    if has_xy and has_e and dxy > 0:
        e_per_mm = abs(de) / dxy
        if dxy >= LAB14_LONG_CONNECTOR_MM and e_per_mm < LAB14_LOW_E_PER_MM:
            return AREA_JUMP_PATH
        if dxy <= LAB14_SHORT_TOP_CONNECTOR_MM and e_per_mm < LAB14_LOW_E_PER_MM and _area_is_top_like(base_area):
            return AREA_SEAM

    return base_area


def _parse_marker_key_values(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"([A-Za-z0-9_]+)=([^\s;]+)", text or ""):
        out[m.group(1).strip()] = m.group(2).strip().strip('"')
    return out


def _parse_clean_temperature_options(text: str) -> dict[str, object]:
    """Parse optional temperature/ooze settings for clean markers.

    Supported examples:
      TEMP=AUTO|OFF|230              target temp before purge/clean
      OOZE_PREVENTION=AUTO|ON|OFF    standby old/inactive tool after retract
      STANDBY_TEMP=AUTO|OFF|200      manual inactive temperature
      TEMP_VARIATION=20              lower inactive tool by 20C
      STANDBY_DELTA=-20              explicit Orca-style delta
      PREHEAT_TIME=AUTO|30           records/uses Orca preheat intent; no forced dwell by default

    E_SPEED_SCALE=AUTO and RETRACT_SPEED_SCALE=AUTO are resolved from the
    converter material-class map for technical Zortrax procedure E moves.
    They do not affect normal print/process speeds.
    """
    kv_raw = _parse_marker_key_values(text or "")
    kv = {k.upper(): v for k, v in kv_raw.items()}
    opts: dict[str, object] = {
        "temp_mode": "AUTO",
        "manual_temp": None,
        "ooze_mode": "AUTO",
        "standby_temp": None,
        "standby_delta": None,
        "preheat_time": None,
        "start_layer": None,
        "skip_first": False,
        "skip_after_toolchange": False,
        "e_speed_scale": None,
        "retract_speed_scale": None,
    }

    # Common v1.2.7 speed scaling options. These scale only E feedrates,
    # not XY cleaning/travel movements.
    _set_speed_scale_options_from_kv(opts, kv)

    if "TEMP" in kv:
        v = kv["TEMP"].strip().upper()
        if v in {"OFF", "NO", "FALSE", "0"}:
            opts["temp_mode"] = "OFF"
        elif v in {"AUTO", "ON", "TRUE", "1"}:
            opts["temp_mode"] = "AUTO"
        else:
            n = first_int(v)
            if n is not None and n > 0:
                opts["temp_mode"] = "MANUAL"
                opts["manual_temp"] = int(n)
    for key in ("OOZE_PREVENTION", "OOZE", "OOZE_PREVENT"):
        if key in kv:
            v = kv[key].strip().upper()
            if v in {"OFF", "NO", "FALSE", "0"}:
                opts["ooze_mode"] = "OFF"
            elif v in {"ON", "YES", "TRUE", "1"}:
                opts["ooze_mode"] = "ON"
            else:
                opts["ooze_mode"] = "AUTO"
    for key in ("STANDBY_TEMP", "IDLE_TEMP", "INACTIVE_TEMP"):
        if key in kv:
            v = kv[key].strip().upper()
            if v in {"OFF", "NO", "FALSE", "0"}:
                opts["standby_temp"] = 0
            elif v in {"AUTO", "ON", "TRUE", "1"}:
                opts["standby_temp"] = None
            else:
                n = first_int(v)
                if n is not None and n > 0:
                    opts["standby_temp"] = int(n)
    for key in ("TEMP_VARIATION", "TEMPERATURE_VARIATION", "STANDBY_DELTA", "OOZE_TEMP_DELTA"):
        if key in kv:
            n = first_int(kv[key])
            if n is not None:
                # positive variation means lower-by-N; negative is used directly
                opts["standby_delta"] = -abs(n) if n > 0 else int(n)
    for key in ("PREHEAT_TIME", "PREHEAT"):
        if key in kv:
            v = kv[key].strip().upper()
            if v in {"AUTO", "ON", "TRUE", "1"}:
                # AUTO means use Orca metadata preheat_time when available.
                # Older v1.2.3 stored -1 here, which printed confusing
                # messages like "Orca preheat_time=-1s" even when Orca was set to 8s.
                opts["preheat_time"] = None
            elif v in {"OFF", "NO", "FALSE", "0"}:
                opts["preheat_time"] = 0
            else:
                n = first_int(v)
                if n is not None and n >= 0:
                    opts["preheat_time"] = int(n)

    # Layer-clean gating. Examples:
    #   ;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 START_LAYER=2 PURGE=AUTO
    #   ;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 SKIP_FIRST=1 PURGE=AUTO
    #   ;ZORTRAX_LAYER_CLEAN AUTO EVERY=5 SKIP_AFTER_TOOLCHANGE=1 PURGE=AUTO
    for key in ("START_LAYER", "MIN_LAYER", "FROM_LAYER", "FIRST_LAYER"):
        if key in kv:
            n = first_int(kv[key])
            if n is not None and n >= 0:
                opts["start_layer"] = int(n)
    for key in ("SKIP_FIRST", "SKIP_FIRST_LAYER", "NO_FIRST_LAYER"):
        if key in kv:
            v = kv[key].strip().upper()
            if v in {"1", "ON", "YES", "TRUE", "AUTO"}:
                opts["skip_first"] = True
                if opts.get("start_layer") is None:
                    opts["start_layer"] = 2
            elif v in {"0", "OFF", "NO", "FALSE"}:
                opts["skip_first"] = False
    for key in ("SKIP_AFTER_TOOLCHANGE", "NO_AFTER_TOOLCHANGE", "SKIP_TOOLCHANGE_LAYER", "SKIP_AFTER_TC"):
        if key in kv:
            v = kv[key].strip().upper()
            if v in {"1", "ON", "YES", "TRUE", "AUTO"}:
                opts["skip_after_toolchange"] = True
            elif v in {"0", "OFF", "NO", "FALSE"}:
                opts["skip_after_toolchange"] = False
    return opts


def _clean_temp_manual_or_auto(meta: GCodeMetadata, tool: int, opts: dict[str, object] | None, *, initial: bool = False, pending_temp: int | None = None) -> int | None:
    opts = opts or {}
    if opts.get("temp_mode") == "OFF":
        return None
    if opts.get("temp_mode") == "MANUAL":
        try:
            return int(opts.get("manual_temp"))
        except Exception:
            return None
    return _tool_target_temp(meta, int(tool), initial=initial, pending_temp=pending_temp)


def _emit_clean_tool_temp(meta: GCodeMetadata, tool: int, opts: dict[str, object] | None, *, initial: bool = False, pending_temp: int | None = None, wait: bool = True) -> list[bytes]:
    temp = _clean_temp_manual_or_auto(meta, int(tool), opts, initial=initial, pending_temp=pending_temp)
    if temp is not None:
        diagnostic_print(f"[temp] clean T{int(tool)} set to {temp}C" + (" and wait" if wait else ""))
    return _emit_tool_temperature(int(tool), temp, wait=wait)


def _ooze_prevention_enabled_for_marker(meta: GCodeMetadata, opts: dict[str, object] | None) -> bool:
    opts = opts or {}
    mode = str(opts.get("ooze_mode", "AUTO")).upper()
    if mode == "OFF":
        return False
    if mode == "ON":
        return True
    return _meta_ooze_prevention_enabled(meta)


def _emit_inactive_tool_standby(meta: GCodeMetadata, old_tool: int | None, opts: dict[str, object] | None) -> list[bytes]:
    if old_tool is None:
        return []
    if not _ooze_prevention_enabled_for_marker(meta, opts):
        return []
    opts = opts or {}
    standby_temp_opt = opts.get("standby_temp")
    if standby_temp_opt == 0:
        return []
    explicit_temp = int(standby_temp_opt) if isinstance(standby_temp_opt, int) and standby_temp_opt > 0 else None
    explicit_delta = opts.get("standby_delta") if isinstance(opts.get("standby_delta"), int) else None
    temp = _standby_temp_for_inactive_tool(meta, int(old_tool), explicit_delta=explicit_delta, explicit_temp=explicit_temp)
    if temp is not None and temp > 0:
        diagnostic_print(f"[ooze] inactive T{int(old_tool)} standby temperature {temp}C")
    return _emit_tool_temperature(int(old_tool), temp, wait=False)


def _emit_toolchange_preheat(meta: GCodeMetadata, target_tool: int, opts: dict[str, object] | None, pending_temp: int | None = None) -> list[bytes]:
    # Orca's preheat_time normally schedules M104 before the toolchange. We cannot
    # move code backwards in post-processing, so we restore the intent by setting
    # the next tool temperature as early as the marker is encountered. The later
    # wait before purge still guarantees the nozzle is at material temperature.
    opts = opts or {}
    if opts.get("temp_mode") == "OFF":
        return []
    preheat_time = opts.get("preheat_time")
    if preheat_time is None:
        preheat_time = _meta_preheat_time(meta)
    temp = _clean_temp_manual_or_auto(meta, int(target_tool), opts, initial=False, pending_temp=pending_temp)
    if temp is not None:
        diagnostic_print(f"[preheat] T{int(target_tool)} set to {temp}C before switch" + (f" (Orca preheat_time={preheat_time}s)" if preheat_time not in (None, 0) else ""))
    return _emit_tool_temperature(int(target_tool), temp, wait=False)

def _tool_from_meta_value(value: str | None) -> int | None:
    if value is None:
        return None
    m = re.search(r"-?\d+", str(value))
    if not m:
        return None
    try:
        n = int(m.group(0))
        return n if n in (0, 1) else None
    except Exception:
        return None

def _first_decimal_from_map(d: dict[str, str], *keys: str) -> Decimal | None:
    for k in keys:
        if k in d and str(d[k]).strip() not in {"", "nil", "None", "none"}:
            val = first_decimal(str(d[k]))
            if val is not None:
                return val
    return None

def _should_defer_clean_marker(mode: str, next_tool: int | None) -> bool:
    if next_tool is None:
        return False
    key = _normalize_marker_token(mode or "AUTO")
    # AUTO/CURRENT in Orca Change filament G-code is normally placed before
    # the emitted T0/T1, so defer it and clean the tool that will become active.
    # DUAL/FULL_DUAL must NOT be deferred into _emit_first_use_clean_for_tool(),
    # because that would collapse a requested full two-head clean into only T0
    # or only T1. DUAL N therefore emits the full Z-Suite dual sequence at
    # the marker when the layer interval allows it; the following T command
    # then selects the tool Orca requested.
    return key in {"AUTO", "CURRENT", "CURRENT_TOOL"}

def _meta_tool_temp(meta: GCodeMetadata, ext: int, initial: bool = True) -> int | None:
    """Return Orca material temperature for a tool.

    Prefer per-tool keys from the ORCA METADATA block, but also support full
    Orca footer comments where values are stored as vectors, e.g.
    `; nozzle_temperature = 250,220`.
    """
    orca = getattr(meta, "orca_metadata", {}) or {}
    bases: list[str] = []
    if initial:
        bases.append("nozzle_temperature_initial_layer")
    bases.append("nozzle_temperature")
    # If initial-layer temperature is missing, fall back to normal temperature;
    # if normal temperature is requested and missing, fall back to initial.
    if not initial:
        bases.append("nozzle_temperature_initial_layer")
    for base in bases:
        val = _orca_value_for_tool(orca, base, int(ext))
        if val is not None and str(val).strip():
            parsed = first_int(str(val))
            if parsed is not None and parsed > 0:
                return parsed
    return None


def _pending_tool_temp(st: AxisState, key: str) -> int | None:
    val = getattr(st, "pending_toolchange_meta", {}).get(key)
    if val is not None and str(val).strip():
        parsed = first_int(str(val))
        if parsed is not None and parsed > 0:
            return parsed
    return None


def _tool_target_temp(meta: GCodeMetadata, tool: int, *, initial: bool = False, pending_temp: int | None = None) -> int | None:
    if pending_temp is not None and pending_temp > 0:
        return int(pending_temp)
    return _meta_tool_temp(meta, int(tool), initial=initial)


def _emit_tool_temperature(tool: int, temp: int | None, *, wait: bool = False) -> list[bytes]:
    if temp is None or int(temp) <= 0:
        return []
    out = [zcmd_simple(8, int(tool), pack_i32(int(temp)))]
    if wait:
        out.append(zcmd_simple(20))
    return out


def _emit_tool_orca_temp(meta: GCodeMetadata, tool: int, *, initial: bool = False, wait: bool = True, pending_temp: int | None = None) -> list[bytes]:
    temp = _tool_target_temp(meta, int(tool), initial=initial, pending_temp=pending_temp)
    if temp is not None:
        diagnostic_print(f"[temp] T{int(tool)} set to Orca material temperature {temp}C" + (" and wait" if wait else ""))
    return _emit_tool_temperature(int(tool), temp, wait=wait)


def _meta_tool_idle_temp(meta: GCodeMetadata, tool: int) -> int | None:
    orca = getattr(meta, "orca_metadata", {}) or {}
    val = _orca_value_for_tool(orca, "idle_temperature", int(tool))
    if val is not None and str(val).strip():
        parsed = first_int(str(val))
        if parsed is not None and parsed > 0:
            return parsed
    return None


def _meta_standby_delta(meta: GCodeMetadata, default: int = -20) -> int:
    orca = getattr(meta, "orca_metadata", {}) or {}
    for key in ("standby_temperature_delta", "temperature_variation", "ooze_temperature_variation", "standby_delta"):
        val = orca.get(key)
        if val is not None and str(val).strip():
            parsed = first_int(str(val))
            if parsed is not None:
                # Orca stores standby_temperature_delta as a negative number, e.g. -20.
                # If a user provides a positive variation, interpret it as lower-by-N.
                return -abs(parsed) if parsed > 0 else parsed
    return int(default)


def _meta_ooze_prevention_enabled(meta: GCodeMetadata) -> bool:
    orca = getattr(meta, "orca_metadata", {}) or {}
    val = orca.get("ooze_prevention")
    if val is None:
        return True
    parsed = parse_bool(str(val))
    return True if parsed is None else bool(parsed)


def _meta_preheat_time(meta: GCodeMetadata) -> int | None:
    orca = getattr(meta, "orca_metadata", {}) or {}
    val = orca.get("preheat_time")
    if val is not None and str(val).strip():
        parsed = first_int(str(val))
        if parsed is not None and parsed > 0:
            return parsed
    return None


def _standby_temp_for_inactive_tool(meta: GCodeMetadata, tool: int, explicit_delta: int | None = None, explicit_temp: int | None = None) -> int | None:
    if explicit_temp is not None and explicit_temp > 0:
        return int(explicit_temp)
    idle = _meta_tool_idle_temp(meta, int(tool))
    if idle is not None:
        return idle
    active_temp = _meta_tool_temp(meta, int(tool), initial=False)
    if active_temp is None:
        return None
    delta = int(explicit_delta) if explicit_delta is not None else _meta_standby_delta(meta)
    return max(0, int(active_temp) + int(delta))

def _parse_start_purge_marker_args(text: str) -> tuple[str, Decimal, Decimal, int | None, int | None, dict[str, object]]:
    # ;ZORTRAX_START_PURGE AUTO LENGTH=60 RETRACT=5
    # PURGE_F and RETRACT_F are optional. If absent, speeds are taken from Orca metadata:
    # deretraction_speed_tN and retraction_speed_tN.
    tokens = text.strip().split()
    mode = "AUTO"
    length = Decimal("60")
    retract = Decimal("0")
    purge_f: int | None = None
    retract_f: int | None = None
    if tokens and "=" not in tokens[0]:
        mode = tokens[0]
        tokens = tokens[1:]
    kv = _parse_marker_key_values(" ".join(tokens))
    if "LENGTH" in kv:
        length = Decimal(str(kv["LENGTH"]))
    elif "PURGE" in kv:
        length = Decimal(str(kv["PURGE"]))
    if "RETRACT" in kv:
        retract = Decimal(str(kv["RETRACT"]))
    if "PURGE_F" in kv:
        purge_f = int(Decimal(str(kv["PURGE_F"])))
    elif "F" in kv:
        purge_f = int(Decimal(str(kv["F"])))
    if "RETRACT_F" in kv:
        retract_f = int(Decimal(str(kv["RETRACT_F"])))
    _mode_tmp, speed_opts = _parse_marker_mode_and_options(text)
    return mode, length, retract, purge_f, retract_f, speed_opts

def _start_purge_tools_for_mode(mode: str, single_material: bool | None) -> list[int]:
    key = _normalize_marker_token(mode or "AUTO")
    if key in {"AUTO", "CURRENT", "CURRENT_TOOL"}:
        return [0] if single_material else [0, 1]
    if key in {"SINGLE", "T0", "MODEL", "0", "TOOL0", "EXTRUDER0"}:
        return [0]
    if key in {"T1", "SUPPORT", "1", "TOOL1", "EXTRUDER1"}:
        return [1]
    if key in {"DUAL", "FULL_DUAL"}:
        return [0, 1]
    raise ValueError(f"Unknown ZORTRAX_START_PURGE mode: {mode!r}")


def _metadata_travel_feedrate(meta: GCodeMetadata) -> int:
    # Existing metadata field is travel_speed_mm_s, not travel_speed_f.
    # Orca travel_speed is mm/s; ZCode feedrate commands use mm/min.
    value = getattr(meta, "travel_speed_mm_s", None)
    if value is not None:
        try:
            dec = Decimal(str(value))
            if dec > 0:
                return int(dec * 60)
        except Exception:
            pass
    value = getattr(meta, "travel_feedrate", None)
    if value is not None:
        try:
            dec = Decimal(str(value))
            if dec > 0:
                return int(dec)
        except Exception:
            pass
    return int(DEFAULT_TRAVEL_FEEDRATE)

def _meta_tool_feedrate(meta: GCodeMetadata, ext: int, kind: str, fallback: int) -> int:
    # Orca metadata speeds are mm/s; metadata parser converts common speeds to mm/min in *_f fields
    # but this helper is defensive and supports both direct metadata and parsed fields.
    if kind == "purge":
        parsed = getattr(meta, f"deretraction_speed_t{ext}_f", None)
        keys = [f"deretraction_speed_t{ext}", f"new_e_f"]
    else:
        parsed = getattr(meta, f"retraction_speed_t{ext}_f", None)
        keys = [f"retraction_speed_t{ext}", f"old_e_f"]
    if isinstance(parsed, int) and parsed > 0:
        return parsed
    orca = getattr(meta, "orca_metadata", {}) or {}
    for key in keys:
        val = orca.get(key)
        if val is None or str(val).strip() == "":
            continue
        try:
            dec = Decimal(str(val))
            if dec <= 0:
                continue
            # Orca extruder speed placeholders are normally mm/s. Convert to mm/min.
            # If value already looks like mm/min from toolchange meta (e.g. new_e_f), keep it.
            if key.endswith("_e_f"):
                return int(dec)
            return int(dec * 60)
        except Exception:
            pass
    return fallback

def _start_purge_drop_position_for_tool(ext: int) -> bytes:
    # Force drop/garbage zone explicitly before start purge.
    # T0/model -> ModelGarbageOutside 0x09
    # T1/support -> SupportGarbageOutside 0x0A
    return zcmd_special_position(0x0A if ext == 1 else 0x09)

def zcmd_start_purge_sequence(
    mode: str,
    meta: GCodeMetadata,
    st: AxisState,
    length: Decimal,
    retract: Decimal,
    purge_f: int | None,
    retract_f: int | None,
    speed_opts: dict[str, object] | None = None,
) -> list[bytes]:
    """START_PURGE for OK reference builds.

    This marker intentionally performs PURGE ONLY:
    - amount is always taken from LENGTH=<mm>;
    - no retract is emitted, even if the marker contains RETRACT=<mm>;
    - before purge, the selected tool is set to the material temperature
      from Orca metadata and a temperature wait command is emitted.
    """
    cmds: list[bytes] = []
    tools = _start_purge_tools_for_mode(mode, meta.single_material)

    # Use relative E so LENGTH is an amount of filament, not an absolute E target.
    cmds.append(zcmd_axis(10, {"E": Decimal(0)}))

    for ext in tools:
        # Select the tool that will be purged.
        if st.active_extruder != ext:
            if ext == 0:
                cmds.extend([zcmd_simple(17, 0x09), zcmd_simple(7, 0)])
            else:
                cmds.extend([zcmd_simple(17, 0x0A), zcmd_simple(7, 1)])
            st.active_extruder = ext

        # Force correct drop/garbage zone independently of START_MACHINE position.
        cmds.append(_start_purge_drop_position_for_tool(ext))

        # Heat the currently purged extruder to material initial-layer temperature
        # from Orca metadata; fallback to normal nozzle temperature.
        temp = _meta_tool_temp(meta, ext, initial=True)
        if temp is not None:
            cmds.append(zcmd_simple(8, ext, pack_i32(int(temp))))
            cmds.append(zcmd_simple(20))

        pf = int(purge_f) if purge_f is not None else _meta_tool_feedrate(meta, ext, "purge", 300)
        pf = _scaled_feedrate(pf, _speed_scale_from_opts(speed_opts, "e_speed_scale", meta=meta, tool=ext, mode="START_PURGE"))
        cmds.append(zcmd_simple(2, pack_i32(int(pf))))
        cmds.append(zcmd_axis_with_values(1, {"E": length}, UNKNOWN_PRINTING_AREA))

        # Intentionally no retract here. RETRACT=<mm> is ignored for START_PURGE
        # in this reference build.

    cmds.append(zcmd_simple(2, pack_i32(int(_metadata_travel_feedrate(meta)))))
    return cmds


def gcode_to_command_stream(
    gcode_path: Path,
    progress: ProgressReporter | None = None,
    start_pct: int = 0,
    end_pct: int = 0,
) -> list[bytes]:
    st = AxisState()
    commands: list[bytes] = []
    stream_meta = parse_metadata_from_gcode(gcode_path)
    lines = gcode_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    total_lines = len(lines)
    has_zortrax_start_machine = any(
        ln.strip().upper().startswith(";ZORTRAX_START_MACHINE") for ln in lines
    )
    before_zortrax_start_machine = bool(has_zortrax_start_machine)

    if progress is not None and end_pct > start_pct:
        progress.update(start_pct, 'Translating G-code to ZCode commands', detail=f'Lines to process: {total_lines}')
    last_pct = start_pct

    for idx, raw in enumerate(lines, 1):
        cmd, comment, params = parse_line(raw)
        out: list[bytes] = []

        if cmd == "COMMENT":
            if comment:
                marker = comment.strip()
                prev_zsuite_layer = getattr(st, "zsuite_layer_index", -1)
                _update_layer_state_from_comment(st, marker)
                upper_marker = marker.upper()
                if upper_marker.startswith("LAYER_CHANGE") and getattr(st, "zsuite_layer_index", -1) != prev_zsuite_layer:
                    out.append(zcmd_simple(16, pack_i32(int(st.zsuite_layer_index))))
                if upper_marker.startswith("ZORTRAX_START_MACHINE"):
                    before_zortrax_start_machine = False
                    mode = marker[len("ZORTRAX_START_MACHINE"):].strip() or "AUTO"
                    try:
                        out.extend(zcmd_start_machine_sequence(mode, stream_meta))
                        _mark_tools_cleaned_after_start(st, mode, stream_meta.single_material)
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_START_PURGE"):
                    mode, length, retract, purge_f, retract_f, speed_opts = _parse_start_purge_marker_args(marker[len("ZORTRAX_START_PURGE"):].strip())
                    try:
                        out.extend(zcmd_start_purge_sequence(mode, stream_meta, st, length, retract, purge_f, retract_f, speed_opts))
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_LOAD_FILAMENT"):
                    marker_args = marker[len("ZORTRAX_LOAD_FILAMENT"):].strip()
                    try:
                        out.extend(zcmd_load_filament_sequence(marker_args, stream_meta, st))
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_END_MACHINE"):
                    mode = marker[len("ZORTRAX_END_MACHINE"):].strip() or "AUTO"
                    try:
                        out.extend(zcmd_end_machine_sequence(mode, stream_meta.single_material))
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_TOOLCHANGE_META"):
                    st.pending_toolchange_meta = _parse_marker_key_values(marker[len("ZORTRAX_TOOLCHANGE_META"):].strip())
                    ln = first_int(st.pending_toolchange_meta.get("layer_num", ""))
                    if ln is not None:
                        st.current_layer = ln
                elif upper_marker.startswith("ZORTRAX_TOOLCHANGE_CLEAN"):
                    marker_args = marker[len("ZORTRAX_TOOLCHANGE_CLEAN"):].strip()
                    mode, _ignored_interval, purge_mm, purge_f, idle_retract_mm, idle_retract_f = _parse_clean_marker_args(marker_args)
                    clean_opts = _parse_clean_temperature_options(marker_args)
                    try:
                        out.extend(_emit_marker_toolchange_clean(
                            st, mode, stream_meta, lines, idx, purge_mm, purge_f, idle_retract_mm, idle_retract_f, clean_opts
                        ))
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_LAYER_CLEAN"):
                    marker_args = marker[len("ZORTRAX_LAYER_CLEAN"):].strip()
                    mode, clean_interval, purge_mm, purge_f, idle_retract_mm, idle_retract_f = _parse_clean_marker_args(marker_args)
                    clean_opts = _parse_clean_temperature_options(marker_args)
                    try:
                        out.extend(_emit_marker_layer_clean(
                            st, mode, clean_interval, stream_meta, purge_mm, purge_f, idle_retract_mm, idle_retract_f, clean_opts, lines, idx
                        ))
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_SPECIAL_CLEAN"):
                    # Legacy compatibility:
                    # - with pending toolchange metadata / next_extruder, behave like TOOLCHANGE_CLEAN;
                    # - otherwise behave like LAYER_CLEAN and honor the optional interval.
                    marker_args = marker[len("ZORTRAX_SPECIAL_CLEAN"):].strip()
                    mode, clean_interval, purge_mm, purge_f, idle_retract_mm, idle_retract_f = _parse_clean_marker_args(marker_args)
                    clean_opts = _parse_clean_temperature_options(marker_args)
                    try:
                        next_tool = _tool_from_meta_value(st.pending_toolchange_meta.get("next_extruder"))
                        if next_tool is not None:
                            out.extend(_emit_marker_toolchange_clean(
                                st, mode, stream_meta, lines, idx, purge_mm, purge_f, idle_retract_mm, idle_retract_f, clean_opts
                            ))
                        else:
                            out.extend(_emit_marker_layer_clean(
                                st, mode, clean_interval, stream_meta, purge_mm, purge_f, idle_retract_mm, idle_retract_f, clean_opts, lines, idx
                            ))
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_SPECIAL_POS"):
                    token = marker[len("ZORTRAX_SPECIAL_POS"):].strip()
                    code = special_position_code_from_token(token)
                    if code is None:
                        raise SystemExit(f"Unknown ZORTRAX_SPECIAL_POS token: {token!r}")
                    out.append(zcmd_special_position(code))
                elif marker.startswith("LAYER:"):
                    try:
                        layer_nr = int(Decimal(marker.split(":", 1)[1].strip()))
                        out.append(zcmd_simple(16, pack_i32(layer_nr)))
                    except Exception:
                        pass

        elif cmd in ("G0", "G1"):
            post_clean_travel_restore = (
                st.pending_post_clean_min_feedrate is not None
                and ("X" in params or "Y" in params)
                and "E" not in params
            )
            prev_x = st.current.get("X", Decimal(0))
            prev_y = st.current.get("Y", Decimal(0))
            prev_e = st.current.get("E", Decimal(0))

            if "F" in params:
                out.append(zcmd_simple(2, pack_i32(int(params["F"]))))
            if post_clean_travel_restore:
                min_f = int(st.pending_post_clean_min_feedrate or 0)
                current_f = int(params["F"]) if "F" in params else 0
                if current_f < min_f:
                    out.append(zcmd_simple(2, pack_i32(min_f)))
                st.pending_post_clean_min_feedrate = None

            vals = {a: st.fix(a, params.get(a)) for a in ("X", "Y", "Z", "E")}
            fan_vals = {"A": params.get("A"), "B": params.get("S") if cmd == "M106" else params.get("B"), "Z2": params.get("Z2")}
            merged = {
                "X": vals["X"], "Y": vals["Y"], "Z": vals["Z"], "E": vals["E"],
                "A": fan_vals["A"], "B": fan_vals["B"], "Z2": fan_vals["Z2"],
            }
            if any(v is not None for v in merged.values()):
                has_xy = ("X" in params) or ("Y" in params)
                has_e = "E" in params
                dx = st.current.get("X", Decimal(0)) - prev_x
                dy = st.current.get("Y", Decimal(0)) - prev_y
                try:
                    dxy = Decimal(str(math.hypot(float(dx), float(dy))))
                except Exception:
                    dxy = Decimal(0)
                de = st.current.get("E", Decimal(0)) - prev_e if has_e else Decimal(0)

                base_area = int(getattr(st, "current_area", UNKNOWN_PRINTING_AREA))
                area = _lab14_motion_area(base_area, has_xy, dxy, has_e, de)

                # LAB08/LAB09 confirmed that excessive FIRST_LAYER_SUPPORT area 0x18
                # in no-raft/no-cool Orca output should be SUPPORT_INFILL.
                if area == AREA_FIRST_LAYER_SUPPORT:
                    area = AREA_SUPPORT_INFILL

                out.append(zcmd_axis_with_values(1, merged, area))

        elif cmd == "G4":
            if "P" in params:
                out.append(zcmd_simple(12, pack_i32(int(params["P"]))))
            elif "S" in params:
                out.append(zcmd_simple(12, pack_i32(int(params["S"] * 1000))))
            else:
                out.append(zcmd_simple(12, pack_i32(0)))

        elif cmd == "G28":
            vals = {a: params.get(a) for a in ("X", "Y", "Z", "E", "A", "B", "Z2") if a in params}
            if not vals:
                # v1.18: bare G28 should be Z-Suite-like safe homing, not 0x7F all axes.
                out.append(zcmd_axis(5, {"X": Decimal(0), "Y": Decimal(0)}))
                out.append(zcmd_axis(5, {"Z": Decimal(0)}))
                st.current.update({"X": Decimal(0), "Y": Decimal(0), "Z": Decimal(0), "E": Decimal(0)})
            else:
                st.current.update({"X": Decimal(0), "Y": Decimal(0), "Z": Decimal(0), "E": Decimal(0)})
                out.append(zcmd_axis(5, vals))

        elif cmd == "G90":
            st.relative = False
            out.append(zcmd_axis(9, {"X": Decimal(0), "Y": Decimal(0), "Z": Decimal(0), "E": Decimal(0), "A": Decimal(0), "B": Decimal(0), "Z2": Decimal(0)}))

        elif cmd == "G91":
            st.relative = True
            out.append(zcmd_axis(10, {"X": Decimal(0), "Y": Decimal(0), "Z": Decimal(0), "E": Decimal(0), "A": Decimal(0), "B": Decimal(0), "Z2": Decimal(0)}))

        elif cmd == "G92":
            vals = {a: params.get(a) for a in ("X", "Y", "Z", "E", "A", "B", "Z2") if a in params}
            if vals:
                for a in ("X", "Y", "Z", "E"):
                    if a in vals:
                        st.current[a] = Decimal(vals[a])
                out.append(zcmd_axis_with_values(4, vals))

        elif cmd == "M2":
            out.append(zcmd_simple(19))

        elif cmd == "M73":
            pass

        elif cmd == "M82":
            st.relative_e = False
            out.append(zcmd_axis(9, {"E": Decimal(0)}))

        elif cmd == "M83":
            st.relative_e = True
            out.append(zcmd_axis(10, {"E": Decimal(0)}))

        elif cmd == "M104" and ("S" in params or "R" in params):
            if before_zortrax_start_machine:
                diagnostic_print("[temp-policy] skipped pre-START_MACHINE Orca M104; ZORTRAX_START_MACHINE will apply Orca/user tool temperatures")
                continue
            temp = params.get("S", params.get("R"))
            ext = int(params["T"]) if "T" in params else st.active_extruder
            out.append(zcmd_simple(8, ext, pack_i32(int(temp))))  # type: ignore[arg-type]

        elif cmd == "M106" and "S" in params:
            raw_s = params["S"]
            try:
                if raw_s < Decimal(0):
                    fan_s = 0
                elif raw_s > Decimal(255):
                    fan_s = 255
                    diagnostic_print(f"[fan] clamped M106 S{raw_s} to S255 for classic ZCode fan axis")
                else:
                    fan_s = int(raw_s.to_integral_value(rounding=ROUND_HALF_UP))
            except Exception:
                fan_s = 0
                diagnostic_print(f"[fan] invalid M106 S{raw_s!r}; using S0")
            out.append(zcmd_axis_with_values(1, {"B": Decimal(fan_s)}, UNKNOWN_PRINTING_AREA))

        elif cmd == "M107":
            out.append(zcmd_axis_with_values(1, {"B": Decimal(0)}, UNKNOWN_PRINTING_AREA))

        elif cmd == "M109":
            if before_zortrax_start_machine:
                diagnostic_print("[temp-policy] skipped pre-START_MACHINE Orca M109; ZORTRAX_START_MACHINE will apply Orca/user temperatures")
                continue
            temp = params.get("S", params.get("R"))
            ext = int(params["T"]) if "T" in params else st.active_extruder
            if st.skip_next_post_toolchange_m109_tool is not None and int(ext) == int(st.skip_next_post_toolchange_m109_tool):
                # Duplicate Orca M109 immediately after our ZORTRAX_TOOLCHANGE_CLEAN.
                # The clean marker already set/waited the same active tool before purge.
                diagnostic_print(f"[toolchange-clean] skipped duplicate post-clean Orca M109 for T{int(ext)}")
                st.skip_next_post_toolchange_m109_tool = None
            else:
                if temp is not None:
                    out.append(zcmd_simple(8, ext, pack_i32(int(temp))))
                out.append(zcmd_simple(20))

        elif cmd == "M110" and "N" in params:
            # LAB09: M110 is G-code line-number reset, not a Z-Suite LAYER command.
            pass

        elif cmd == "M140" and ("S" in params or "R" in params):
            if before_zortrax_start_machine:
                diagnostic_print("[temp-policy] skipped pre-START_MACHINE Orca M140; ZORTRAX_START_MACHINE will apply chamber")
                continue
            temp = params.get("S", params.get("R"))
            out.append(zcmd_simple(14, pack_i32(int(temp))))  # type: ignore[arg-type]

        elif cmd == "M141" and ("S" in params or "R" in params):
            if before_zortrax_start_machine:
                diagnostic_print("[temp-policy] skipped pre-START_MACHINE Orca M141; ZORTRAX_START_MACHINE will apply chamber")
                continue
            temp = params.get("S", params.get("R"))
            out.append(zcmd_simple(22, pack_i32(int(temp))))  # type: ignore[arg-type]

        elif cmd == "M190":
            if before_zortrax_start_machine:
                diagnostic_print("[temp-policy] skipped pre-START_MACHINE Orca M190 wait; ZORTRAX_START_MACHINE will apply chamber/wait")
                continue
            temp = params.get("S", params.get("R"))
            if temp is not None:
                out.append(zcmd_simple(14, pack_i32(int(temp))))
            out.append(zcmd_simple(20))

        elif cmd == "M191":
            if before_zortrax_start_machine:
                diagnostic_print("[temp-policy] skipped pre-START_MACHINE Orca M191 wait; ZORTRAX_START_MACHINE will apply chamber/wait")
                continue
            temp = params.get("S", params.get("R"))
            if temp is not None:
                out.append(zcmd_simple(22, pack_i32(int(temp))))
            out.append(zcmd_simple(20))

        elif cmd in ("T0", "T1"):
            ext = int(cmd[1:])
            old_ext = st.active_extruder
            idle_mm = st.pending_idle_retract_mm
            idle_f = st.pending_idle_retract_f
            if ext != st.active_extruder:
                # v1.04: optionally retract the tool that is becoming inactive before
                # the physical tool switch, then unretract the newly active tool if it
                # had been retracted during an earlier switch.
                if idle_mm == Decimal("-1"):
                    idle_mm = ZSUITE_IDLE_RETRACT_AUTO_MM
                out.extend(zcmd_idle_retract_before_toolchange(st, old_ext, idle_mm, _resolve_special_clean_retract_f(idle_f) if idle_mm is not None else idle_f))
                fast = 3 if ext == 0 else 4
                slow = 1 if ext == 0 else 2
                out += [
                    zcmd_simple(2, pack_i32(_travel_feedrate_from_meta(stream_meta, "AUTO"))),
                    zcmd_simple(17, fast),
                    zcmd_simple(2, pack_i32(500)),
                    zcmd_simple(17, slow),
                    zcmd_simple(7, ext),
                ]
                st.active_extruder = ext
                out.extend(zcmd_idle_unretract_after_toolchange(st, ext, _tool_deretract_feedrate_from_meta(stream_meta, ext, idle_f)))
                # v9: Even when ;ZORTRAX_SPECIAL_CLEAN AUTO N skips cleaning
                # on this layer, the normal tool-switch block above still ends
                # through the slow F500/special-position path. Z-Suite restores
                # travel speed before the head returns to the model/wipe area.
                # Therefore every real T0/T1 switch needs a one-shot return
                # speed guard; a following actual clean will simply replace it.
                st.pending_post_clean_min_feedrate = post_clean_min_feedrate("T1" if ext == 1 else "T0", stream_meta)
            else:
                # Embedded Z-Suite start/clean sequences may already leave the
                # requested tool active. Do not emit a redundant slow switching block.
                pass
            if st.pending_clean_tool == ext:
                out.extend(_emit_first_use_clean_for_tool(st, ext, stream_meta, force=True, purge_mm=st.pending_clean_purge_mm, purge_f=st.pending_clean_purge_f))
                st.pending_clean_tool = None
                st.pending_clean_mode = None
                st.pending_clean_purge_mm = None
                st.pending_clean_purge_f = None
                st.pending_idle_retract_mm = None
                st.pending_idle_retract_f = None
                st.pending_toolchange_meta = {}
            if st.pending_clean_tool is None:
                st.pending_idle_retract_mm = None
                st.pending_idle_retract_f = None

        commands.extend(out)

        if progress is not None and end_pct > start_pct and total_lines > 0:
            pct = _scaled_percent(idx, total_lines, start_pct, max(start_pct, end_pct - 2))
            if pct > last_pct:
                progress.update(pct, 'Translating G-code to ZCode commands')
                last_pct = pct

    if progress is not None and end_pct > start_pct:
        progress.update(max(start_pct, end_pct - 1), 'Injecting report markers')
    return append_report_progress(commands)

def build_default_classic_header(command_count: int, print_time: int, device_id: int) -> bytes:
    """
    Byte-identical defaults extracted from the classic Inventure ZCode header layout.
    The metadata patch step overwrites the project-confirmed fields afterward.
    """
    buf = bytearray(128)
    buf[:5] = b"ZCode"
    write_int_le(buf, 16, 1, 1)
    write_int_le(buf, 17, 1, 0)
    write_int_le(buf, 18, 4, STEPS["X"])
    write_int_le(buf, 22, 4, STEPS["Y"])
    write_int_le(buf, 26, 4, STEPS["Z"])
    write_int_le(buf, 30, 4, STEPS["E"])
    write_int_le(buf, 34, 4, STEPS["A"])
    write_int_le(buf, 38, 4, STEPS["B"])
    write_int_le(buf, 42, 4, STEPS["Z2"])
    write_int_le(buf, 46, 4, 0)
    write_int_le(buf, 50, 4, command_count)
    write_int_le(buf, 54, 4, print_time)
    write_int_le(buf, 58, 1, 0)
    write_int_le(buf, 59, 1, 0)
    write_int_le(buf, 60, 1, 0)
    write_int_le(buf, 61, 1, device_id)
    write_int_le(buf, 62, 1, 101)
    write_int_le(buf, 63, 1, 0)
    write_int_le(buf, 64, 1, 1)
    write_int_le(buf, 65, 1, 0)
    write_int_le(buf, 66, 1, 0)
    write_int_le(buf, 67, 1, 0)
    write_int_le(buf, 68, 1, 1)
    write_int_le(buf, 69, 1, 12)
    write_int_le(buf, 70, 1, 1)
    write_int_le(buf, 71, 1, 0)
    write_int_le(buf, 72, 1, 0)
    write_int_le(buf, 73, 4, 1)
    write_int_le(buf, 77, 4, 1)
    write_int_le(buf, 81, 4, 0)
    write_int_le(buf, 85, 1, 1)
    write_int_le(buf, 86, 1, 0)
    buf[127] = crc8_d5(bytes(buf[:127]))
    return bytes(buf)

def generate_classic_zcode_pure_python(
    gcode_path: Path,
    output_zcode: Path,
    device_name: str,
    log: bool = False,
    progress: ProgressReporter | None = None,
) -> None:
    if device_name.upper() != "INVENTURE":
        raise SystemExit("This pure-Python path currently targets classic Inventure only.")
    if progress is not None:
        progress.update(20, 'Reading normalized G-code', detail=f'Input work file: {gcode_path.name}')
    commands = gcode_to_command_stream(gcode_path, progress=progress, start_pct=24, end_pct=58)
    if progress is not None:
        progress.update(60, 'Parsing metadata for classic header')
    meta = parse_metadata_from_gcode(gcode_path)
    print_time = int(meta.print_time or 0)
    if progress is not None:
        progress.update(66, 'Building default classic ZCode header', detail=f'Commands: {len(commands)}')
    header = build_default_classic_header(len(commands), print_time, DEVICE_IDS["INVENTURE"])
    if progress is not None:
        progress.update(70, 'Writing pure-Python .zcode stream', detail=f'Output file: {output_zcode.name}')
    with output_zcode.open("wb") as f:
        f.write(header)
        total_cmds = len(commands)
        last_pct = 70
        for idx, c in enumerate(commands, 1):
            f.write(c)
            if progress is not None and total_cmds > 0:
                pct = _scaled_percent(idx, total_cmds, 70, 78)
                if pct > last_pct:
                    progress.update(pct, 'Writing pure-Python .zcode stream')
                    last_pct = pct
    if progress is not None:
        progress.update(78, 'Pure-Python conversion finished', detail=f'Generated command stream: {len(commands)} commands')
    if log:
        if progress is not None:
            progress.break_line()
        console_print(f"Generated {output_zcode.name} with {len(commands)} commands (pure Python classic path)")

# ---------------------------------------------------------------------------
# CLI / output naming
# ---------------------------------------------------------------------------

def sanitize_filename_component(text: str) -> str:
    text = text.strip()
    text = re.sub(r'[<>:"/\\|?*]+', '_', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip(' .') or 'output'

def parse_seconds_to_orca_time(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts: list[str] = []
    if h:
        parts.append(f"{h}h")
    if m or h:
        parts.append(f"{m}m")
    if s and not h:
        parts.append(f"{s}s")
    return ''.join(parts) if parts else '0s'

def is_orca_pp_path(path: Path) -> bool:
    return path.name.lower().endswith('.gcode.pp')


def derive_output_filename_from_metadata(input_path: Path) -> str | None:
    try:
        meta = parse_metadata_from_gcode(input_path)
    except Exception:
        return None
    orca = meta.orca_metadata
    input_base = orca.get('input_filename_base') or orca.get('model_name') or orca.get('plate_name')
    layer = orca.get('layer_height')
    filament_t0 = orca.get('filament_t0') or orca.get('filament_type_t0')
    filament_t1 = orca.get('filament_t1') or orca.get('filament_type_t1')
    time_str = parse_seconds_to_orca_time(meta.print_time)
    parts = [input_base, layer, filament_t0, filament_t1, time_str]
    parts = [sanitize_filename_component(p) for p in parts if p]
    if len(parts) >= 4:
        return '_'.join(parts) + '.zcode'
    return None

def derive_output_filename_without_env(input_path: Path) -> str:
    if is_orca_pp_path(input_path):
        meta_name = derive_output_filename_from_metadata(input_path)
        if meta_name:
            return meta_name
    name = input_path.name
    if name.lower().endswith('.gcode.pp'):
        return name[:-3].rsplit('.', 1)[0] + '.zcode'
    return sanitize_filename_component(input_path.with_suffix('.zcode').name)


def _strip_env_path_quotes(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip().strip('"').strip("'")
    return s or None


def normalize_output_filename(name: str) -> str | None:
    try:
        base = Path(name).name
    except Exception:
        base = name
    if not base:
        return None
    lower = base.lower()
    if lower.endswith('.gcode.3mf'):
        base = base[:-10] + '.zcode'
    elif lower.endswith('.gcode.pp'):
        base = base[:-3].rsplit('.', 1)[0] + '.zcode'
    elif lower.endswith('.gcode'):
        base = base[:-6] + '.zcode'
    elif not lower.endswith('.zcode'):
        base = Path(base).stem + '.zcode'
    return sanitize_filename_component(base)


def derive_output_path_from_orca_env(input_path: Path) -> tuple[Path | None, str | None]:
    output_name = derive_output_filename_without_env(input_path)
    env_candidates = [
        ('SLIC3R_PP_OUTPUT_PATH', os.environ.get('SLIC3R_PP_OUTPUT_PATH')),
        ('ORCA_OUTPUT_PATH', os.environ.get('ORCA_OUTPUT_PATH')),
        ('SLIC3R_PP_OUTPUT', os.environ.get('SLIC3R_PP_OUTPUT')),
        ('ORCA_OUTPUT', os.environ.get('ORCA_OUTPUT')),
        ('SLIC3R_PP_OUTPUT_NAME', os.environ.get('SLIC3R_PP_OUTPUT_NAME')),
        ('ORCA_OUTPUT_NAME', os.environ.get('ORCA_OUTPUT_NAME')),
    ]
    for env_name, raw_value in env_candidates:
        raw = _strip_env_path_quotes(raw_value)
        if not raw:
            continue
        target = Path(raw)
        raw_lower = raw.lower()
        if env_name.endswith('_PATH'):
            if target.suffix:
                target.parent.mkdir(parents=True, exist_ok=True)
                normalized_name = normalize_output_filename(target.name) or output_name
                return target.with_name(normalized_name), f'{env_name} full path'
            target.mkdir(parents=True, exist_ok=True)
            return target / output_name, f'{env_name} directory'
        if raw_lower.endswith(('.gcode', '.gcode.pp', '.gcode.3mf', '.zcode')):
            normalized_name = normalize_output_filename(target.name) or output_name
            target.parent.mkdir(parents=True, exist_ok=True)
            return target.with_name(normalized_name), f'{env_name} full path'
        if os.path.isabs(raw) or '/' in raw or '\\' in raw:
            target.mkdir(parents=True, exist_ok=True)
            return target / output_name, f'{env_name} directory-like path'
    return None, None


def derive_output_path(input_path: Path) -> tuple[Path, str]:
    if is_orca_pp_path(input_path):
        env_path, env_source = derive_output_path_from_orca_env(input_path)
        if env_path is None:
            raise SystemExit(
                'Orca output path is not available in the environment. '
                'This converter now requires Orca to provide the final Save/Save As output path for .gcode.pp inputs.'
            )
        return env_path, f'auto ({env_source})'
    return input_path.with_name(derive_output_filename_without_env(input_path)), 'input directory'


def resolve_input_output_paths(args: argparse.Namespace) -> tuple[Path, Path, str]:
    input_raw = args.input_opt or args.input_file
    if not input_raw:
        raise SystemExit("Missing input .gcode. Pass it as the only positional argument for Orca post-processing, or use -i/--input.")
    gcode = Path(input_raw)
    if args.output:
        out = Path(args.output)
        source = 'explicit --output'
    else:
        out, source = derive_output_path(gcode)
    return gcode, out, source

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Pure-Python Inventure converter for the classic .zcode path. "
            "It keeps the latest metadata patching/report logic and preserves Orca "
            "post-processing compatibility."
        )
    )
    ap.add_argument("input_file", nargs="?", help="Input .gcode when invoked directly by Orca post-processing")
    ap.add_argument("-i", "--input", dest="input_opt", help="Input .gcode from Orca")
    ap.add_argument("-o", "--output", help="Output .zcode")
    ap.add_argument("-d", "--device", default="INVENTURE")
    ap.add_argument("--software-version", default="2.32.0.0")
    ap.add_argument("-l", "--log", action="store_true")
    ap.add_argument("--dump-meta", action="store_true", help="Print parsed metadata as JSON after patching")
    ap.add_argument("--keep-work", action="store_true", help="Keep temporary normalized/converted G-code work copy")
    return ap

def main() -> int:
    print(f"Zortrax Inventure Orca converter {SCRIPT_VERSION}", flush=True)
    args = build_arg_parser().parse_args()
    default_log = Path(__file__).with_name('orca_postprocess_last.log')
    set_log_file(os.environ.get('G2Z_LOG_FILE') or str(default_log))
    console_print(f"Zortrax Inventure Orca converter version: {SCRIPT_VERSION}")
    for item in SCRIPT_CHANGELOG:
        _append_log_line(f"- {item}")
    gcode, out, out_source = resolve_input_output_paths(args)
    if not gcode.exists():
        raise SystemExit(f"Missing input: {gcode}")

    progress = ProgressReporter(enabled=True)
    progress.update(0, 'Starting converter', detail=f'Input: {gcode.name}')
    progress.update(4, 'Validating paths', detail=f'Output: {out}')
    progress.update(10, 'Preparing work copy')
    work_gcode, temp_dir, m83_path_used = maybe_prepare_working_gcode(gcode, preserve_temp=args.keep_work)
    try:
        if work_gcode == gcode:
            progress.update(14, 'Work copy ready', detail='Using original G-code directly')
        else:
            detail = f'Prepared normalized work copy: {work_gcode.name}'
            if m83_path_used:
                detail += '\nRelative-E input detected and converted to Orca-like M82 for processing'
            progress.update(14, 'Work copy ready', detail=detail)

        progress.update(18, 'Starting pure-Python conversion', detail=f'Device: {args.device}')
        generate_classic_zcode_pure_python(work_gcode, out, args.device, log=args.log, progress=progress)

        progress.update(82, 'Parsing original metadata for final header patch')
        meta = parse_metadata_from_gcode(gcode)
        software = parse_software_version(args.software_version)
        progress.update(86, 'Applying Inventure header patch', detail=f'Software version: {args.software_version}')
        patch_classic_zcode(out, meta, software, DEVICE_IDS['INVENTURE'])
        progress.update(89, 'Reading final header CRC')
        header_crc = out.read_bytes()[OFFSET_HEADER_CRC]

        progress.break_line()
        console_print(f"Patched {out.name}: {build_report(meta, header_crc)}")
        console_print(f"Output path: {out} (mode: {out_source})")
        if m83_path_used:
            console_print('Work copy path used: relative-E input detected; converted to Orca-like M82 before pure-Python conversion.')
        if meta.orca_metadata:
            console_print(f"Detected ORCA METADATA keys: {', '.join(sorted(meta.orca_metadata.keys()))}")
        if getattr(meta, "zsuite_hints", None):
            console_print(f"Detected ZSUITE HINT keys: {', '.join(sorted(meta.zsuite_hints.keys()))}")
        if args.dump_meta:
            progress.update(90, 'Dumping parsed metadata')
            progress.break_line()
            console_print(json.dumps(meta.to_dict(), indent=2, sort_keys=True))
        progress.finish('Finished', detail=f'Saved: {out.name}')
        return 0
    finally:
        if temp_dir is not None and not args.keep_work:
            shutil.rmtree(temp_dir, ignore_errors=True)


# v1.17 override: Orca 2.4.0-dev/macOS plate bed temperatures are vectors.
# Metadata uses bed_temp_<plate>_initial_t0/t1 and bed_temp_<plate>_t0/t1.
def _apply_bed_temperature_metadata(meta: GCodeMetadata, orca: dict[str, str]) -> None:
    curr = orca.get("curr_bed_type")
    if curr:
        meta.curr_bed_type = curr
        meta.mark("ORCA_METADATA:curr_bed_type")

    prefix = _plate_prefix_from_curr_bed_type(curr)

    # Prefer T0 for actual bed target because Zortrax Inventure has one bed.
    # T1 is kept in metadata for diagnostics/dual parity but is not required for single.
    prefix_to_keys = {
        "supertack": (
            ["bed_temp_supertack_initial_t0", "bed_temp_supertack_initial", "bed_temp_supertack_initial_t1"],
            ["bed_temp_supertack_t0", "bed_temp_supertack", "bed_temp_supertack_t1"],
        ),
        "cool": (
            ["bed_temp_cool_initial_t0", "bed_temp_cool_initial", "bed_temp_cool_initial_t1"],
            ["bed_temp_cool_t0", "bed_temp_cool", "bed_temp_cool_t1"],
        ),
        "textured_cool": (
            ["bed_temp_textured_cool_initial_t0", "bed_temp_textured_cool_initial", "bed_temp_textured_cool_initial_t1"],
            ["bed_temp_textured_cool_t0", "bed_temp_textured_cool", "bed_temp_textured_cool_t1"],
        ),
        "eng": (
            ["bed_temp_eng_initial_t0", "bed_temp_eng_initial", "bed_temp_eng_initial_t1"],
            ["bed_temp_eng_t0", "bed_temp_eng", "bed_temp_eng_t1"],
        ),
        "hot": (
            ["bed_temp_hot_initial_t0", "bed_temp_hot_initial", "bed_temp_hot_initial_t1"],
            ["bed_temp_hot_t0", "bed_temp_hot", "bed_temp_hot_t1"],
        ),
        "textured": (
            ["bed_temp_textured_initial_t0", "bed_temp_textured_initial", "bed_temp_textured_initial_t1"],
            ["bed_temp_textured_t0", "bed_temp_textured", "bed_temp_textured_t1"],
        ),
    }

    initial_keys: list[str] = []
    other_keys: list[str] = []
    if prefix and prefix in prefix_to_keys:
        iks, oks = prefix_to_keys[prefix]
        initial_keys.extend(iks)
        other_keys.extend(oks)

    # fallback order if curr_bed_type absent/unrecognized
    for p in ("hot", "eng", "textured", "textured_cool", "cool", "supertack"):
        iks, oks = prefix_to_keys[p]
        for k in iks:
            if k not in initial_keys:
                initial_keys.append(k)
        for k in oks:
            if k not in other_keys:
                other_keys.append(k)

    initial, initial_key = _first_int_from_meta(orca, initial_keys)
    other, other_key = _first_int_from_meta(orca, other_keys)

    if initial is not None:
        meta.bed_temp_initial = initial
        meta.bed_temp_source = initial_key
        meta.mark(f"ORCA_METADATA:bed_temp_initial:{initial_key}")
    if other is not None:
        meta.bed_temp_other = other
        meta.mark(f"ORCA_METADATA:bed_temp_other:{other_key}")


if __name__ == "__main__":
    raise SystemExit(main())
