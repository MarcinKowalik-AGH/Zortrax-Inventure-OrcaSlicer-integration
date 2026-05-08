#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, hashlib, shutil
root=Path(__file__).resolve().parents[1]
conv=root/'converter/g2z_wrapper_orca.py'
gcode=root/'tests/single_lab38/source_gcode/cone_0.15_Z-PLA_Z-PLA_37m40s sup.gcode'
ref=root/'tests/single_lab38/zcode/CONE_SUPPORT__V38_01_REFERENCE_CONFIRMED.zcode'
out=root/'tests/single_lab38/zcode/reproduced_by_v1.4.1_check.zcode'
if out.exists(): out.unlink()
subprocess.check_call([sys.executable,str(conv),'-i',str(gcode),'-o',str(out)])
hr=hashlib.sha256(ref.read_bytes()).hexdigest(); ho=hashlib.sha256(out.read_bytes()).hexdigest()
print('reference sha256:',hr)
print('generated sha256:',ho)
print('byte-for-byte equal:',ref.read_bytes()==out.read_bytes())
raise SystemExit(0 if hr==ho else 1)
