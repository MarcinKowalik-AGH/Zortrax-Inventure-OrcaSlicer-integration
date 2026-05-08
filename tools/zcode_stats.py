#!/usr/bin/env python3
from pathlib import Path
import sys, collections, hashlib
AREA_NAMES={0x0B:'RAFT_BOTTOM',0x0D:'RAFT_INTERFACE',0xDF:'SEAM',0xFB:'JUMP_PATH',0x1D:'WASTE_TOWER_MODEL',0x1E:'WASTE_TOWER_SUPPORT'}
def stats(path):
    b=Path(path).read_bytes(); pos=128; ops=collections.Counter(); areas=collections.Counter(); cmds=0
    while pos < len(b):
        ln=b[pos]
        if ln<2 or pos+ln>=len(b): break
        op=b[pos+1]; ops[op]+=1; cmds+=1
        if op==1 and ln>=4: areas[b[pos+2]]+=1
        pos += ln+1
    print(path)
    print(' size:',len(b),'sha256:',hashlib.sha256(b).hexdigest())
    print(' header_count:',int.from_bytes(b[50:54],'little'),'actual_commands:',cmds,'byte72:',b[72],'58..60:',b[58:61].hex(' '),'crc127:',b[127])
    print(' op_LAYER_0x10:',ops[0x10],'op_PAUSE_0x0F:',ops[0x0F])
    for k,n in sorted(areas.items()):
        if k in AREA_NAMES or n>0:
            print(f' area 0x{k:02X} {AREA_NAMES.get(k,"")}: {n}')
if __name__=='__main__':
    for p in sys.argv[1:]: stats(p)
