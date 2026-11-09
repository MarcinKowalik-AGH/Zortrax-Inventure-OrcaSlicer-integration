#!/usr/bin/env python3
"""Second pass for the missing illustrated Zortrax PDFs; preserve a failed-download report."""
import concurrent.futures, gzip, hashlib, json, time
from pathlib import Path
import requests
OUT=Path("extra_zortrax_pdf")
TASKS=[
 ("M300_Dual","M300_Dual_Extruder_Disassembly_Maintenance.pdf","27120"),
 ("Inventure","Inventure_Nozzle_Replacement.pdf","16254"),
 ("M300","M300_Platform_Maintenance_27_pages.pdf","13541"),
 ("M300","M300_Extruder_PCB_Replacement.pdf","9402"),
 ("M300_Dual","M300_Dual_Axes_Maintenance.pdf","30823"),
 ("Inventure","Inventure_Hotend_Module_Replacement.pdf","15379"),
 ("Inventure","Inventure_Complete_Extruder_Replacement.pdf","15818"),
]
for m in ("M300","M300_Dual","Inventure"):(OUT/m).mkdir(parents=True,exist_ok=True)
HEAD={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36","Accept":"application/pdf,application/octet-stream,*/*;q=0.7"}
def fetch(item):
 model,name,pid=item
 original=f"https://support.zortrax.com/pdf/create/steps.php?id={pid}"
 o={"model":model,"filename":name,"official_original":original,"status":"failed","attempts":[]}
 for ts in ("20261108000000","20250101000000","20230101000000"):
  url=f"https://web.archive.org/web/{ts}id_/{original}"
  try:
   r=requests.get(url,headers=HEAD,timeout=(7,13),allow_redirects=True)
   if r.status_code!=200:raise ValueError(f"HTTP {r.status_code}")
   data=r.content
   if data.startswith(b"\x1f\x8b"):data=gzip.decompress(data)
   if not data.startswith(b"%PDF-") or len(data)<15000 or b"%%EOF" not in data[-10000:]:
    raise ValueError(f"invalid / incomplete PDF ({len(data)} bytes)")
   p=OUT/model/name;p.write_bytes(data)
   o.update(status="downloaded",source=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
   print(f"OK {model} {name} {len(data)}",flush=True)
   return o
  except Exception as ex:
   msg=repr(ex)[:175]
   o["attempts"].append({"url":url,"error":msg})
   print(f"FAILED {model} {name} {ts} {msg}",flush=True)
   if "429" in msg:break
   time.sleep(1.0)
 return o
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
 records=list(ex.map(fetch,TASKS))
result={"downloaded":[r for r in records if r["status"]=="downloaded"],"failed":[r for r in records if r["status"]=="failed"]}
(OUT/"DOWNLOAD_MANIFEST.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
(OUT/"RAPORT_POBRANIA.txt").write_text("Second pass original Zortrax Support Center PDF snapshots\n"+"\n".join(f"{x['status']}: {x['model']}/{x['filename']} | {x['official_original']}" for x in records)+"\n",encoding="utf8")
print("RESULTS",len(result["downloaded"]),"downloaded",len(result["failed"]),"failed",flush=True)
