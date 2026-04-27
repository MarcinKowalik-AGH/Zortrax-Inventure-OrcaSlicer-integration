
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

SCRIPT_VERSION = "v1.01"
SCRIPT_CHANGELOG = [
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

MATERIAL_CODE_MAP = {
    # Native Zortrax
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
    # Support / open material map from project findings
    "BASF ULTRAFUSE BVOH": 0x17,
    "ABS-BASED FILAMENT": 0x81,
    "GLASS-TYPE FILAMENT": 0x84,
    "FLEX-BASED FILAMENT": 0x85,
    "PLA-BASED FILAMENT": 0x86,
    "PETG-BASED FILAMENT": 0x87,
    "NYLON-BASED FILAMENT": 0x89,
    "ULTRAT-BASED FILAMENT": 0x91,
    "ESD PETG-BASED FILAMENT": 0x92,
    "PLA PRO-BASED FILAMENT": 0x94,
    "ASA PRO-BASED FILAMENT": 0x95,
    "SEMIFLEX-BASED FILAMENT": 0x96,
}

MATERIAL_ALIASES = {
    "Z ULTRAT PLUS": "Z-ULTRAT PLUS",
    "Z SUPPORT": "Z-SUPPORT",
    "Z SUPPORT PLUS": "Z-SUPPORT PLUS",
    "Z SUPPORT PREMIUM": "Z-SUPPORT PREMIUM",
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


def material_code_from_name(name: str) -> int:
    if not name:
        return 0
    key = normalize_material_name(name)
    if key in MATERIAL_CODE_MAP:
        return MATERIAL_CODE_MAP[key]
    alias = MATERIAL_ALIASES.get(key)
    return MATERIAL_CODE_MAP.get(alias, 0) if alias else 0


def infer_fw_triplet(meta: GCodeMetadata) -> tuple[int, int, int]:
    support_enabled = bool(meta.support_enabled)
    support_code = meta.support_code or 0
    if support_enabled and support_code in {0x07, 0x0D, 0x11}:
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
    meta.process = orca.get("process")

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
    meta = GCodeMetadata(orca_metadata=parse_orca_metadata(lines))
    _apply_filename_fallback(meta, gcode_path)
    _apply_orca_block(meta)
    _apply_comment_fallbacks(meta, lines)
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

ZS_START_SINGLE_HEX = """
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

ZS_START_DUAL_HEX = """
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

ZS_START_MACHINE_SEQUENCES = {
    "SINGLE": _zcmds_from_hex_blob(ZS_START_SINGLE_HEX),
    "DUAL": _zcmds_from_hex_blob(ZS_START_DUAL_HEX),
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

def zcmd_start_machine_sequence(mode: str, single_material: bool | None) -> list[bytes]:
    return list(ZS_START_MACHINE_SEQUENCES[_machine_mode_key(mode, single_material)])

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
        self.pending_post_clean_min_feedrate: int | None = None
        self.pending_toolchange_meta: dict[str, str] = {}

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
            out.append(zcmd_simple(11, pack_i32(p)))
            p += 1
        out.append(cmd)
    if p == 100:
        out.append(zcmd_simple(11, pack_i32(100)))
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
    key = _machine_mode_key(mode, single_material)
    if key == "SINGLE":
        st.cleaned_tools.add(0)
        st.active_extruder = 0
    else:
        # Observed behavior in the current same-STL dual test: the Z-Suite-like
        # start sequence ends with/supports T1 prepared. T0 must still be cleaned
        # at its first real use.
        st.cleaned_tools.add(1)
        st.active_extruder = 1

def _emit_first_use_clean_for_tool(st: AxisState, tool: int, meta: GCodeMetadata, force: bool = False, purge_mm: Decimal | None = None, purge_f: int | None = None) -> list[bytes]:
    if not force and tool in st.cleaned_tools:
        return []
    mode = "T1" if tool == 1 else "T0"
    out = zcmd_special_clean_sequence(mode, tool, meta.single_material)
    resolved_purge_f = _tool_deretract_feedrate_from_meta(meta, tool, purge_f) if purge_mm is not None else purge_f
    out.extend(zcmd_purge_sequence(st, purge_mm, resolved_purge_f))
    out.extend(zcmd_post_clean_restore_sequence(mode, meta))
    st.pending_post_clean_min_feedrate = post_clean_min_feedrate(mode, meta)
    st.cleaned_tools.add(tool)
    st.active_extruder = tool
    return out


def _parse_clean_marker_args(arg_text: str) -> tuple[str, int | None, Decimal | None, int | None, Decimal | None, int | None]:
    """Parse ;ZORTRAX_SPECIAL_CLEAN MODE [N] [PURGE[=mm]] [PURGE_F=feedrate] [IDLE_RETRACT=mm] [IDLE_RETRACT_F=feedrate].

    Examples:
      ;ZORTRAX_SPECIAL_CLEAN AUTO
      ;ZORTRAX_SPECIAL_CLEAN AUTO 10
      ;ZORTRAX_SPECIAL_CLEAN AUTO 10 PURGE=8 PURGE_F=360 IDLE_RETRACT=3 IDLE_RETRACT_F=900
      ;ZORTRAX_SPECIAL_CLEAN DUAL EVERY=5 PURGE

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


def _clean_allowed_on_current_layer(st: AxisState, interval: int | None) -> bool:
    if interval is None:
        return True
    if st.current_layer <= 0:
        # Do not accidentally suppress start/pre-layer cleaning if Orca did not
        # expose layer state yet.
        return True
    return (st.current_layer % interval) == 0


def _update_layer_state_from_comment(st: AxisState, marker: str) -> None:
    txt = marker.strip()
    if txt.upper().startswith("LAYER_CHANGE"):
        st.current_layer += 1
        return
    m = re.match(r"(?i)^layer\s*#\s*(\d+)", txt)
    if m:
        try:
            st.current_layer = int(m.group(1))
        except Exception:
            pass


def _parse_marker_key_values(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"([A-Za-z0-9_]+)=([^\s;]+)", text or ""):
        out[m.group(1).strip()] = m.group(2).strip().strip('"')
    return out

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
    keys = []
    if initial:
        keys.append(f"nozzle_temperature_initial_layer_t{ext}")
    keys.append(f"nozzle_temperature_t{ext}")
    orca = getattr(meta, "orca_metadata", {}) or {}
    for key in keys:
        val = orca.get(key)
        if val is not None and str(val).strip():
            parsed = first_int(str(val))
            if parsed is not None and parsed > 0:
                return parsed
    return None

def _parse_start_purge_marker_args(text: str) -> tuple[str, Decimal, Decimal, int | None, int | None]:
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
    return mode, length, retract, purge_f, retract_f

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

    if progress is not None and end_pct > start_pct:
        progress.update(start_pct, 'Translating G-code to ZCode commands', detail=f'Lines to process: {total_lines}')
    last_pct = start_pct

    for idx, raw in enumerate(lines, 1):
        cmd, comment, params = parse_line(raw)
        out: list[bytes] = []

        if cmd == "COMMENT":
            if comment:
                marker = comment.strip()
                _update_layer_state_from_comment(st, marker)
                upper_marker = marker.upper()
                if upper_marker.startswith("ZORTRAX_START_MACHINE"):
                    mode = marker[len("ZORTRAX_START_MACHINE"):].strip() or "AUTO"
                    try:
                        out.extend(zcmd_start_machine_sequence(mode, stream_meta.single_material))
                        _mark_tools_cleaned_after_start(st, mode, stream_meta.single_material)
                    except ValueError as exc:
                        raise SystemExit(str(exc)) from exc
                elif upper_marker.startswith("ZORTRAX_START_PURGE"):
                    mode, length, retract, purge_f, retract_f = _parse_start_purge_marker_args(marker[len("ZORTRAX_START_PURGE"):].strip())
                    try:
                        out.extend(zcmd_start_purge_sequence(mode, stream_meta, st, length, retract, purge_f, retract_f))
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
                elif upper_marker.startswith("ZORTRAX_SPECIAL_CLEAN"):
                    mode, clean_interval, purge_mm, purge_f, idle_retract_mm, idle_retract_f = _parse_clean_marker_args(marker[len("ZORTRAX_SPECIAL_CLEAN"):].strip())
                    if purge_mm == Decimal("-1"):
                        purge_mm = _first_decimal_from_map(st.pending_toolchange_meta, "flush_length", "first_flush_volume", "second_flush_volume")
                    if idle_retract_mm == Decimal("-1"):
                        idle_retract_mm = _first_decimal_from_map(st.pending_toolchange_meta, "old_retract", "new_retract")
                    try:
                        next_tool = _tool_from_meta_value(st.pending_toolchange_meta.get("next_extruder"))
                        if next_tool is None:
                            next_tool = _next_tool_command(lines, idx)
                        if not _clean_allowed_on_current_layer(st, clean_interval):
                            # Clean is skipped by layer interval, but optional IDLE_RETRACT
                            # is a toolchange pressure-control feature and should still apply
                            # to the next real T0/T1 switch.
                            if next_tool is not None and idle_retract_mm is not None:
                                st.pending_idle_retract_mm = idle_retract_mm
                                st.pending_idle_retract_f = idle_retract_f
                        elif _clean_allowed_on_current_layer(st, clean_interval):
                            if _should_defer_clean_marker(mode, next_tool):
                                st.pending_clean_tool = next_tool
                                st.pending_clean_mode = mode
                                st.pending_clean_purge_mm = purge_mm
                                st.pending_clean_purge_f = purge_f
                                st.pending_idle_retract_mm = idle_retract_mm
                                st.pending_idle_retract_f = idle_retract_f
                            else:
                                key = _normalize_marker_token(mode or "AUTO")
                                if key in {"AUTO", "CURRENT", "CURRENT_TOOL"}:
                                    out.extend(_emit_first_use_clean_for_tool(st, st.active_extruder, stream_meta, force=True, purge_mm=purge_mm, purge_f=purge_f))
                                elif key in {"T0", "MODEL", "0", "TOOL0", "EXTRUDER0"}:
                                    out.extend(_emit_first_use_clean_for_tool(st, 0, stream_meta, force=True, purge_mm=purge_mm, purge_f=purge_f))
                                elif key in {"T1", "SUPPORT", "1", "TOOL1", "EXTRUDER1"}:
                                    out.extend(_emit_first_use_clean_for_tool(st, 1, stream_meta, force=True, purge_mm=purge_mm, purge_f=purge_f))
                                elif key in {"DUAL", "FULL_DUAL", "DUAL_FULL"}:
                                    # Manual full dual clean outside Orca's pre-T toolchange hook.
                                    out.extend(zcmd_special_clean_sequence(mode, st.active_extruder, stream_meta.single_material))
                                    out.extend(zcmd_purge_sequence(st, purge_mm, _tool_deretract_feedrate_from_meta(stream_meta, st.active_extruder, purge_f) if purge_mm is not None else purge_f))
                                    st.active_extruder = marker_final_active_tool(mode, stream_meta.single_material, st.active_extruder)
                                    out.extend(zcmd_post_clean_restore_sequence(mode, stream_meta))
                                    st.pending_post_clean_min_feedrate = post_clean_min_feedrate(mode, stream_meta)
                                    st.cleaned_tools.update({0, 1})
                                else:
                                    out.extend(zcmd_special_clean_sequence(mode, st.active_extruder, stream_meta.single_material))
                                    out.extend(zcmd_purge_sequence(st, purge_mm, _tool_deretract_feedrate_from_meta(stream_meta, st.active_extruder, purge_f) if purge_mm is not None else purge_f))
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
                out.append(zcmd_axis_with_values(1, merged, UNKNOWN_PRINTING_AREA))

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
            temp = params.get("S", params.get("R"))
            ext = int(params["T"]) if "T" in params else st.active_extruder
            out.append(zcmd_simple(8, ext, pack_i32(int(temp))))  # type: ignore[arg-type]

        elif cmd == "M106" and "S" in params:
            out.append(zcmd_axis_with_values(1, {"B": params["S"]}, UNKNOWN_PRINTING_AREA))

        elif cmd == "M107":
            out.append(zcmd_axis_with_values(1, {"B": Decimal(0)}, UNKNOWN_PRINTING_AREA))

        elif cmd == "M109":
            temp = params.get("S", params.get("R"))
            ext = int(params["T"]) if "T" in params else st.active_extruder
            if temp is not None:
                out.append(zcmd_simple(8, ext, pack_i32(int(temp))))
            out.append(zcmd_simple(20))

        elif cmd == "M110" and "N" in params:
            out.append(zcmd_simple(16, pack_i32(int(params["N"]))))

        elif cmd == "M140" and ("S" in params or "R" in params):
            temp = params.get("S", params.get("R"))
            out.append(zcmd_simple(14, pack_i32(int(temp))))  # type: ignore[arg-type]

        elif cmd == "M141" and ("S" in params or "R" in params):
            temp = params.get("S", params.get("R"))
            out.append(zcmd_simple(22, pack_i32(int(temp))))  # type: ignore[arg-type]

        elif cmd == "M190":
            temp = params.get("S", params.get("R"))
            if temp is not None:
                out.append(zcmd_simple(14, pack_i32(int(temp))))
            out.append(zcmd_simple(20))

        elif cmd == "M191":
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
                out.extend(zcmd_idle_retract_before_toolchange(st, old_ext, idle_mm, _tool_retract_feedrate_from_meta(stream_meta, old_ext, idle_f) if idle_mm is not None else idle_f))
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
    write_int_le(buf, 72, 1, 6)
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
