#!/usr/bin/env python3
from __future__ import annotations

# Zortrax Inventure / Orca v1.4.16-load-filament-marker-2026-05-06 wrapper
# Delegates mechanical conversion to the bundled LAB14/v1.2.7-compatible converter,
# then applies all confirmed preview/body rules: seam, raft carry/cleanup, tower split,
# and exact ;PAUSE_PRINT -> OP0F pauses.

import importlib.util, sys, math, re, collections
from pathlib import Path

SCRIPT_VERSION = "v1.4.16-production-load-filament-marker-2026-05-06"

# Extracted from Z-Suite static UI resources.  Keep this separate from the
# classic .zcode header device id used by the converter/base module.  In Z-Suite
# UI enum, Inventure is 1, while the confirmed classic .zcode header[61] for our
# Inventure workflow remains 0x0A.
ZSUITE_UI_PRINTER_MODEL_IDS = {
    "M200": 0,
    "INVENTURE": 1,
    "M350": 2,
    "M300_PL": 3,
    "M300_CN": 4,
    "M200_PLUS": 5,
    "M300_PLUS": 6,
    "INKSPIRE": 7,
    "M300_DUAL": 8,
    "APOLLER": 9,
    "ENDUREAL": 11,
    "INKSPIRE_2": 12,
    "CUSTOM_RESIN": 250,
}

# Names observed in Z-Suite classic configuration metadata.  These are diagnostic
# aliases only; motion generation still uses the byte/procedure rules confirmed
# on real .zcode/printer tests.
ZSUITE_CLASSIC_CONFIG_KEYS = {
    "model_retract_before_toolchange": "ES_RetractionBeforeChangeToModel",
    "model_retract_before_toolchange_speed": "ES_RetractionBeforeChangeToModelSpeed",
    "support_retract_before_toolchange": "ES_RetractionBeforeChangeToSupport",
    "support_retract_before_toolchange_speed": "ES_RetractionBeforeChangeToSupportSpeed",
    "purge_after_change_to_model": "ES_PurgeAfterChangeToModel",
    "purge_after_change_to_model_speed": "ES_PurgeAfterChangeToModelSpeed",
    "purge_after_change_to_support": "ES_PurgeAfterChangeToSupport",
    "purge_after_change_to_support_speed": "ES_PurgeAfterChangeToSupportSpeed",
    "sleep_before_brushing": "ES_SleepTimeBeforeBrusning",
    "brushing_times": "ES_BrushingTimes",
    "firmware_extruder_switch": "ES_ExtruderSwitchInFirmware",
    "waste_tower_enable": "ES_WasteTowerEnable",
    "waste_tower_size_x": "ES_WasteTowerSizeX",
    "waste_tower_size_y": "ES_WasteTowerSizeY",
    "waste_tower_center_x": "ES_WasteTowerCenterX",
    "waste_tower_center_y": "ES_WasteTowerCenterY",
    "waste_tower_offset": "ES_WasteTowerOffset",
    "waste_tower_speed_model": "ES_WasteTowerSpeedModel",
    "waste_tower_speed_support": "ES_WasteTowerSpeedSupport",
    "waste_tower_feed_model": "ES_WasteTowerFeedModel",
    "waste_tower_feed_support": "ES_WasteTowerFeedSupport",
    "inventure_back_fan_speed": "InventureBackFanSpeed",
    "support_temp_extruder": "SupportTempExtruder",
    "low_temp_support": "LowTempSupport",
    "warming_time_from_low_temp_support": "WarmingTimeFromLowTempSupport",
    "warming_margin_time_from_low_temp_support": "WarmingMarginTimeFromLowTempSupport",
}

# Profile suffix policy: Orca user copies may append a suffix after canonical preset names.
# Examples: "Z-PLA test", "0.15mm Quality ... - dual test", "Zortrax Inventure ... - single copy".
PROFILE_SUFFIX_POLICY = "CANONICAL_PREFIX_PLUS_USER_SUFFIX_ALLOWED"

STEPS={'X':640,'Y':640,'Z':802,'E':960,'A':1,'B':1,'Z2':1}
AXES=['X','Y','Z','E','A','B','Z2']
BITS={'X':1,'Y':2,'Z':4,'E':8,'A':16,'B':32,'Z2':64}
SUPPORT_AREAS={0x04,0x05,0x06,0x07,0x18,0x20}
RAFT_INPUT_AREAS={0xFF,0x05,0x07,0x18,0x04,0x06,0x20}
CANDIDATE_SEAM_AREAS={0x00,0x01,0x02,0x03,0x0E,0x0F,0x14,0x15,0x16,0x17,0x19,0x1A,0xFB}
AREA_NAMES={0x00:'MODEL_CONTOUR',0x01:'VISIBLE_INFILL',0x02:'MODEL_INVISIBLE_CONTOUR',0x03:'INVISIBLE_INFILL',0x04:'SUPPORT_CONTOUR',0x05:'SUPPORT_INFILL',0x06:'SUPPORT_INTERFACE_CONTOUR',0x07:'SUPPORT_INTERFACE_INFILL',0x0A:'RAFT',0x0B:'RAFT_BOTTOM',0x0D:'RAFT_INTERFACE',0x0E:'VISIBLE_TOP_INFILL',0x0F:'VISIBLE_BOTTOM_INFILL',0x18:'FIRST_LAYER_SUPPORT',0x1D:'WASTE_TOWER_MODEL',0x1E:'WASTE_TOWER_SUPPORT',0x1F:'WASTE_TOWER_RAFT',0x20:'SUPPORT_BOTTOM_INFILL',0xDF:'SEAM',0xFB:'JUMP_PATH',0xFC:'JUMP'}


# Z-Suite OP02/feedrate semantic map, confirmed by project native samples and b1/b3 print-speed/support-speed comparison.
# LOG_ONLY: these constants document mapping for reports/presets; converter motion generation still uses confirmed byte-level rules.
ZSUITE_OP02_SPEED_SEMANTICS = {
    0x00: ("outer_wall_speed", "global_print_speed_scaled"),
    0x02: ("inner_wall_speed", "global_print_speed_scaled"),
    0x03: ("internal_solid_infill_speed", "global_print_speed_scaled"),
    0x11: ("top_surface_speed", "global_print_speed_scaled"),
    0x13: ("sparse_infill_speed", "global_print_speed_scaled"),
    0x04: ("support_speed", "global_print_speed_x_support_print_speed"),
    0x05: ("support_speed", "global_print_speed_x_support_print_speed"),
    0x18: ("support_speed", "global_print_speed_x_support_print_speed"),
    0x06: ("support_related_global_speed", "global_print_speed_scaled_not_support_slider"),
    0x07: ("support_related_global_speed", "global_print_speed_scaled_not_support_slider"),
    0x09: ("support_related_global_speed", "global_print_speed_scaled_not_support_slider"),
    0x1B: ("support_interface_speed", "global_print_speed_scaled_not_support_slider"),
    0x21: ("support_interface_speed", "global_print_speed_scaled_not_support_slider"),
    0x1D: ("wipe_tower_max_purge_speed", "tower_fixed_F2000"),
    0x1E: ("wipe_tower_max_purge_speed", "tower_fixed_F2000"),
    0xFC: ("travel_speed", "travel_fixed_F7200"),
}

def crc8_d5(data: bytes) -> int:
    c=0; poly=0xD5
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c<<1)^poly)&0xFF if c&0x80 else (c<<1)&0xFF
    return c

def pop(x:int)->int:
    """Compatibility popcount for macOS /usr/bin/python3 without int.bit_count()."""
    x = int(x)
    if x < 0:
        x = -x
    try:
        return x.bit_count()
    except AttributeError:
        count = 0
        while x:
            x &= x - 1
            count += 1
        return count

def iter_cmds(buf: bytes):
    pos=128
    while pos < len(buf):
        ln=buf[pos]
        if ln < 2 or pos+ln >= len(buf):
            raise ValueError(f'bad command at pos={pos}, len={ln}, size={len(buf)}')
        yield pos, ln, bytes(buf[pos:pos+ln+1])
        pos += ln+1

def set_area(b: bytearray, pos:int, ln:int, area:int):
    b[pos+2]=area&0xFF; b[pos+ln]=crc8_d5(bytes(b[pos:pos+ln]))

def cmd_pause(layer:int, zfloor:int) -> bytes:
    core=bytes([0x0A,0x0F]) + int(layer).to_bytes(4,'little',signed=True) + int(zfloor).to_bytes(4,'little',signed=True)
    return core + bytes([crc8_d5(core)])

def patch_header_count_crc(buf: bytearray, add:int):
    old=int.from_bytes(buf[50:54],'little')
    buf[50:54]=int(old+add).to_bytes(4,'little')
    buf[127]=crc8_d5(bytes(buf[:127]))
    return old, old+add, buf[127]

def parse_bool(s): return str(s).strip().lower() in ('1','true','yes','on')

def gcode_info(path: Path):
    cur_layer=None; cur_z=None; zmap={}; pause=[]; meta={}; hints={}; filament_profiles=[]; in_meta=False; in_hints=False; seam_by_layer=collections.defaultdict(list); seam_all=[]
    with path.open(errors='ignore') as f:
        for i,line in enumerate(f,1):
            s=line.strip()
            up=s.upper()
            if s.startswith('; ===== ORCA METADATA BEGIN'): in_meta=True
            elif s.startswith('; ===== ORCA METADATA END'): in_meta=False
            elif up == '; ===== ZORTRAX ZSUITE HINTS BEGIN =====':
                in_hints=True
                continue
            elif up == '; ===== ZORTRAX ZSUITE HINTS END =====':
                in_hints=False
                continue
            elif in_meta and s.startswith(';') and '=' in s:
                k,v=s[1:].split('=',1); meta[k.strip()]=v.strip()
            if s.startswith(';ZORTRAX_FILAMENT_PROFILE'):
                prof={}
                for key,val in re.findall(r'([A-Za-z0-9_]+)=([^\s]+)', s):
                    prof[key.lower()]=val.strip().strip('"')
                if prof:
                    filament_profiles.append(prof)
            if s.startswith(';') and '=' in s:
                k0,v0=s[1:].split('=',1); key0=k0.strip()
                if in_hints or key0.lower().startswith('zsuite_'):
                    hints[key0.lower()]=v0.strip().strip('"')
            m2=re.match(r'^;\s*([^=]+?)\s*=\s*(.+)$',s)
            if m2 and m2.group(1).strip() not in meta:
                meta[m2.group(1).strip()]=m2.group(2).strip()
            if s.startswith(';ZORTRAX_LAYER_META'):
                m=re.search(r'layer_num=([-0-9]+)\s+layer_z=([-0-9.]+)',s)
                if m: cur_layer=int(m.group(1)); cur_z=float(m.group(2)); zmap[cur_layer]=cur_z
            if ';PAUSE_PRINT' in s:
                pause.append({'line':i,'layer_zero_based':cur_layer,'visible_layer_1based':None if cur_layer is None else cur_layer+1,'z':cur_z})
            if 'move inwards before retraction/seam' in s:
                mx=re.search(r'X(-?\d+(?:\.\d+)?)',s); my=re.search(r'Y(-?\d+(?:\.\d+)?)',s)
                if mx and my and cur_layer is not None:
                    x=float(mx.group(1)); y=float(my.group(1)); seam_by_layer[cur_layer].append((x,y,i)); seam_all.append({'line':i,'layer_zero_based':cur_layer,'x':x,'y':y})
    try: raft_layers=int(float(str(meta.get('raft_layers','0')).strip()))
    except Exception: raft_layers=0
    support_enabled=parse_bool(meta.get('support', meta.get('enable_support','false')))
    return {'zmap':zmap,'pause_markers':pause,'metadata':meta,'zsuite_hints':hints,'filament_profiles':filament_profiles,'seam_by_layer':seam_by_layer,'seam_comments':seam_all,'raft_layers':raft_layers,'support_enabled':support_enabled}

def zfloor_for(layer:int,zmap:dict):
    if layer in zmap: return int(math.floor(zmap[layer]+1e-9))
    lows=[k for k in zmap if k<=layer]
    return int(math.floor(zmap[max(lows)]+1e-9)) if lows else 0

def patch_semantics(buf: bytes, info: dict):
    b=bytearray(buf); cur={a:0 for a in AXES}; rel={a:False for a in AXES}; layer=None; active_tool=0
    raft_layers=int(info.get('raft_layers') or 0); support_enabled=bool(info.get('support_enabled')); seam_by_layer=info.get('seam_by_layer',{})
    report=collections.Counter()
    pos=128
    while pos < len(b):
        ln=b[pos]
        if ln<2 or pos+ln>=len(b): break
        c=bytes(b[pos:pos+ln+1]); op=c[1]
        if op in (9,10) and ln>=3:
            bit=c[2]
            for a in AXES:
                if bit & BITS[a]: rel[a]=(op==10)
        elif op==5 and ln>=3:
            bit=c[2]
            for a in AXES:
                if bit & BITS[a]: cur[a]=0
        elif op==7 and ln>=3:
            active_tool=c[2]
        elif op==16 and ln>=6:
            layer=int.from_bytes(c[2:6],'little',signed=True)
        elif op in (1,4):
            area=None; bit=None; vals=[]
            if op==1 and (ln-4)%4==0:
                area=c[2]; bit=c[3]; n=(ln-4)//4
                if pop(bit)==n and 4+n*4==ln:
                    off=4
                    for a in AXES:
                        if bit & BITS[a]: vals.append((a,int.from_bytes(c[off:off+4],'little',signed=True))); off+=4
            elif op==4 and (ln-3)%4==0:
                bit=c[2]; n=(ln-3)//4
                if pop(bit)==n and 3+n*4==ln:
                    off=3
                    for a in AXES:
                        if bit & BITS[a]: vals.append((a,int.from_bytes(c[off:off+4],'little',signed=True))); off+=4
            if vals:
                dx=dy=de=0.0; has_xy=False; has_e=False
                for a,val in vals:
                    old=cur[a]
                    if op==4: delta=val-old; new=val
                    elif rel[a]: delta=val; new=old+val
                    else: delta=val-old; new=val
                    if a=='X': dx=delta/STEPS[a]; has_xy=True
                    elif a=='Y': dy=delta/STEPS[a]; has_xy=True
                    elif a=='E': de=delta/STEPS[a]; has_e=True
                    cur[a]=new
                if op==1 and area is not None:
                    new_area=area; dxy=math.hypot(dx,dy); positive=has_xy and has_e and de>0.00001 and dxy>0.00001
                    if raft_layers>0 and layer is not None and 0 <= layer < raft_layers:
                        split=max(1,raft_layers//2); raft_area=0x0B if layer<split else 0x0D
                        if positive and new_area in RAFT_INPUT_AREAS:
                            new_area=raft_area; report['raft_print_to_class']+=1
                        elif (not positive) and new_area in SUPPORT_AREAS:
                            new_area=0xFB; report['raft_nonprint_to_jump']+=1
                    if new_area==0x1D and active_tool==1 and positive:
                        new_area=0x1E; report['tower_t1_to_support']+=1
                    if new_area in (0x1D,0x1E,0x1F) and has_xy and ((not has_e) or de<=1e-7 or (dxy>0 and de/max(dxy,1e-9)<0.0005)):
                        new_area=0xFB; report['tower_connector_to_jump']+=1
                    if new_area in CANDIDATE_SEAM_AREAS and layer is not None and has_xy and (not has_e or de<=1e-7) and 0.01 <= dxy <= 1.8:
                        x=cur['X']/640; y=cur['Y']/640; best=None
                        for sx,sy,line in seam_by_layer.get(layer,[]):
                            dist=math.hypot(x-sx,y-sy)
                            if best is None or dist < best[0]: best=(dist,sx,sy,line)
                        if best and best[0] <= 0.35:
                            new_area=0xDF; report['seam_to_0xDF']+=1
                    if new_area != area: set_area(b,pos,ln,new_area)
        pos += ln+1
    return bytes(b), dict(report)

def insert_exact_gcode_pauses(buf: bytes, info: dict):
    targets=[]
    for idx,m in enumerate(info.get('pause_markers',[]),1):
        layer=m.get('layer_zero_based')
        if layer is None: continue
        targets.append({'idx':idx,'line':m['line'],'layer':layer,'visible_layer_1based':layer+1,'zfloor':zfloor_for(layer,info.get('zmap',{})),'source_z':m.get('z')})
    by_layer=collections.defaultdict(list)
    for t in targets: by_layer[t['layer']].append(t)
    out=bytearray(buf[:128]); inserted=[]
    for pos,ln,c in iter_cmds(buf):
        out.extend(c)
        if c[1]==0x10 and ln>=6:
            lay=int.from_bytes(c[2:6],'little',signed=True)
            for t in by_layer.get(lay,[]):
                pc=cmd_pause(lay,t['zfloor']); out.extend(pc); inserted.append({**t,'pause_cmd':pc.hex(' ')})
    patch_header_count_crc(out,len(inserted))
    return bytes(out), {'target_count':len(targets),'inserted_count':len(inserted),'targets':targets,'inserted':inserted}


def audit_zsuite_static_compat(buf: bytes, info: dict):
    """Log-only audit based on static Z-Suite names and confirmed printer tests.

    This function must not change generated .zcode.  Its purpose is to catch the
    exact class of regression fixed in v1.4.2: single-material T0 clean must not
    silently receive the dual T0 clean/load-like markers area F4 + dwell 3000.
    """
    meta = info.get('metadata', {}) or {}
    hints = info.get('zsuite_hints', {}) or {}
    mode = str(meta.get('mode', '')).strip().upper()
    single_hint = (mode == 'SINGLE') or (not bool(info.get('support_enabled')) and str(meta.get('filament_t1','')).strip() in ('', '0', 'None'))
    counts = collections.Counter()
    for _pos, ln, c in iter_cmds(buf):
        op = c[1]
        if op == 1 and ln >= 4:
            area = c[2]
            if area == 0xF4:
                counts['area_F4_E_move'] += 1
        elif op == 12 and ln >= 6:
            try:
                dwell_ms = int.from_bytes(c[2:6], 'little', signed=True)
            except Exception:
                dwell_ms = None
            if dwell_ms == 3000:
                counts['dwell_3000'] += 1
    status = 'OK'
    if single_hint and (counts['area_F4_E_move'] or counts['dwell_3000']):
        status = 'WARNING_SINGLE_HAS_DUAL_T0_MARKERS'
    return {
        'status': status,
        'mode_metadata': mode or 'UNKNOWN',
        'single_hint': bool(single_hint),
        'zsuite_ui_printer_model_id_inventure': ZSUITE_UI_PRINTER_MODEL_IDS['INVENTURE'],
        'zcode_header_device_id': buf[61] if len(buf) > 61 else None,
        'area_F4_E_move_count': int(counts['area_F4_E_move']),
        'dwell_3000_count': int(counts['dwell_3000']),
        'zsuite_hints_count': len(hints),
        'zortrax_filament_profile_count': len(info.get('filament_profiles', []) or []),
        'zsuite_hint_keys': sorted(hints.keys()),
        'zsuite_hint_policy': str(hints.get('zsuite_hint_policy', hints.get('zsuite_policy', 'LOG_ONLY'))).upper() if hints else 'NONE',
    }


def main() -> int:
    here=Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    base_path=here/'g2z_wrapper_orca_base_lab14_known_good.py'
    if not base_path.exists():
        raise SystemExit(f'Missing bundled base converter: {base_path}')
    spec=importlib.util.spec_from_file_location('zortrax_base', base_path)
    base=importlib.util.module_from_spec(spec); sys.modules['zortrax_base']=base; assert spec.loader; spec.loader.exec_module(base)
    args=base.build_arg_parser().parse_args()
    gcode,out,_source=base.resolve_input_output_paths(args)
    print(f'Zortrax Inventure Orca converter {SCRIPT_VERSION}')
    ret=base.main()
    if ret != 0: return ret
    if not out.exists():
        raise SystemExit(f'Base converter finished but output not found: {out}')
    info=gcode_info(gcode)
    raw=out.read_bytes()
    patched, semantics=patch_semantics(raw, info)
    patched, pause_report=insert_exact_gcode_pauses(patched, info)
    out.write_bytes(patched)
    print('Applied confirmed beta3 postprocess rules:')
    print(f'  raft_layers={info.get("raft_layers")} support_enabled={info.get("support_enabled")}')
    print(f'  semantics={semantics}')
    print(f'  ;PAUSE_PRINT markers={pause_report["target_count"]}, inserted OP0F pauses={pause_report["inserted_count"]}')
    zsuite_audit = audit_zsuite_static_compat(patched, info)
    print('Z-Suite static compatibility audit:')
    print(f'  ui_printer_model_id(Inventure)={zsuite_audit["zsuite_ui_printer_model_id_inventure"]}, zcode_header_device_id=0x{zsuite_audit["zcode_header_device_id"]:02X}')
    print(f'  single_hint={zsuite_audit["single_hint"]}, area_F4_E_moves={zsuite_audit["area_F4_E_move_count"]}, dwell_3000={zsuite_audit["dwell_3000_count"]}, status={zsuite_audit["status"]}')
    print(f'  zsuite_hints={zsuite_audit["zsuite_hints_count"]}, filament_profiles={zsuite_audit.get("zortrax_filament_profile_count",0)}, policy={zsuite_audit["zsuite_hint_policy"]}')
    if zsuite_audit["zsuite_hint_keys"]:
        print(f'  zsuite_hint_keys={", ".join(zsuite_audit["zsuite_hint_keys"])}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
