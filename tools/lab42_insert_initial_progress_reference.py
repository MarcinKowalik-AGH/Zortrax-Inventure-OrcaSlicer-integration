from pathlib import Path
import json, zipfile, shutil, os

def crc8_d5(data):
 c=0; poly=0xD5
 for b in data:
  c ^= b
  for _ in range(8): c=((c<<1)^poly)&0xFF if c&0x80 else (c<<1)&0xFF
 return c
src=Path('/mnt/data/cone_dual_ZPLA_ZSUPPORT_raft50_v13beta3_LAB42_LAYER_OPENFIX.zcode')
out=Path('/mnt/data/cone_dual_ZPLA_ZSUPPORT_raft50_v13beta3_LAB42B_OPENFIX_LAYERS_PROGRESS.zcode')
b=bytearray(src.read_bytes())
cmd=bytes.fromhex('03 0B 00 15')
if b[128:132] != cmd:
 b=b[:128]+bytearray(cmd)+b[128:]
 old=int.from_bytes(b[50:54],'little')
 b[50:54]=int(old+1).to_bytes(4,'little')
# ensure dual-open fields
b[58:61]=bytes([1,2,1])
b[72]=0
b[127]=crc8_d5(bytes(b[:127]))
out.write_bytes(b)
# report counts
pos=128; cnt=0; ops={}
while pos < len(b):
 ln=b[pos]
 if ln<2 or pos+ln>=len(b): break
 op=b[pos+1]; ops[op]=ops.get(op,0)+1; cnt+=1; pos+=ln+1
report={'output':str(out),'size':len(b),'header_count':int.from_bytes(b[50:54],'little'),'actual_cmds':cnt,'58_60':b[58:61].hex(' '),'byte72':b[72],'crc':b[127],'first20':[], 'op16_count':ops.get(16,0), 'op11_count':ops.get(11,0)}
pos=128
for i in range(20):
 ln=b[pos]; report['first20'].append(b[pos:pos+ln+1].hex(' ')); pos+=ln+1
Path('/mnt/data/cone_LAB42B_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
