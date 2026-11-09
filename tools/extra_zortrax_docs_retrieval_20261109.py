#!/usr/bin/env python3
"""Download additional printable Zortrax service PDFs from discovered third-party mirrors.
Only actual complete PDFs are packed. A separately labeled report lists inaccessible material.
"""
import concurrent.futures, gzip, hashlib, json, re, time
from pathlib import Path
from urllib.parse import quote
import requests

OUT=Path("extra_zortrax_pdf")
CANDIDATES=[
 ("M300","Extruder_PCB_Replacement_ManualsPlus.pdf","https://manuals.plus/m/2f95ab425716a3778bcdd7b46bf222d97fbd2a1e1fae841a2c6296766332dbf2.pdf","14-page OEM procedure mirrored by ManualsPlus"),
 ("M300","Side_Covers_Installation_ManualsPlus.pdf","https://manuals.plus/m/358e3a832fdc59087bb0b6708bf3b142ec7e1f923c843b73427ce8c2cfa25216.pdf","10-page OEM procedure mirrored by ManualsPlus"),
 ("M300","Side_Covers_Installation_Alternative.pdf","https://manuals.plus/m/3657d25bee9c2b7d5b967cbe082dead8bc453366e8370f7d1955fa0769b8ae65.pdf","Alternative edition of side covers instruction"),
 ("M300","M_Series_Firmware_Error_Messages.pdf","https://manuals.plus/m/71a7c0381303d597c923bb82902fdd73289626a7f7ca5be7420db8e512266036.pdf","M Series firmware error messages and fault handling"),
 ("M300","M_Series_2017_User_Guide.pdf","https://manuals.plus/m/b54b5c89ee1b79223e33e93ec759af26219e159e2b40f443972fca5296e22686.pdf","Historical original M Series owner guide"),
 ("M300","M_Series_2018_User_Guide_Mirror.pdf","https://manuals.plus/m/ad347d7befa7a45e033c09f70d318ac7ddea5c4263f609b3a5af8e17607ed1b6.pdf","M Series owner guide mirror: possible duplicate"),
 ("M300_Dual","M300_Dual_User_Guide_2020_ManualsPlus.pdf","https://manuals.plus/m/2ebc2ff3fd85cfbb7fe0a4aa1083f0a03ff6c8b7446262051dc5110b0b83b0f0.pdf","2020 M300 Dual owner guide (some websites incorrectly label as M300 Plus)"),
 ("Inventure","Inventure_User_Guide_2019_ManualsPlus.pdf","https://manuals.plus/m/cff1b270280de3dcdb093d6364678f84282c6d20958e412ad9511775925205bb.pdf","2019 Inventure 57 page user guide"),
 ("Inventure","Inventure_User_Guide_2020_ManualsPlus.pdf","https://manuals.plus/m/8a39ffaf9b55d633ffa275a5f09d679d2c4f7585004f490677cfccf9a7f0f568.pdf","2020 Inventure 55 page user guide"),
]
ORIGINAL_PAGES=[
 ("M300","M300_Platform_Maintenance_27_pages.pdf","m300-platform-maintenance"),
 ("M300","M300_Heatbed_Cable_Replacement.pdf","m200-heatbed-cable-replacement"),
 ("M300","M300_Display_Panel_Replacement.pdf","m-series-display-panel-replacement"),
 ("M300","M300_Manual_Platform_Calibration.pdf","platform-calibration"),
 ("M300_Dual","M300_Dual_Extruder_Disassembly_Maintenance.pdf","extruder-maintenance"),
 ("M300_Dual","M300_Dual_Axes_Maintenance.pdf","axes-maintenance-m300-dual"),
 ("Inventure","Inventure_Nozzle_Replacement.pdf","inventure-nozzle-replacement"),
 ("Inventure","Inventure_Hotend_Module_Replacement.pdf","hotend-module-replacement"),
 ("Inventure","Inventure_Extruder_Replacement.pdf","extruder-replacement"),
 ("Inventure","Inventure_Waste_Brushes_Replacement.pdf","waste-container-brushes-replacement"),
]
for m in ("M300","M300_Dual","Inventure"):
 (OUT/m).mkdir(parents=True,exist_ok=True)
HEAD={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36","Accept":"application/pdf,text/html;q=0.9,*/*;q=0.8","Referer":"https://manuals.plus/","Accept-Encoding":"gzip, deflate"}
results=[]
def valid_pdf(content):
 if content[:2]==b"\x1f\x8b":
  try: content=gzip.decompress(content)
  except Exception: pass
 if not content.startswith(b"%PDF-") or len(content)<18000: raise ValueError(f"Not a PDF: {len(content)} bytes, {content[:35]!r}")
 if b"%%EOF" not in content[-10000:]:raise ValueError(f"Truncated PDF: no EOF in last 10K (bytes={len(content)})")
 return content
def retrieve(task):
 model,filename,url,description=task
 o={"model":model,"filename":filename,"url":url,"description":description,"status":"failed"}
 for attempt in range(2):
  try:
   r=requests.get(url,headers=HEAD,timeout=(8,24),allow_redirects=True)
   r.raise_for_status()
   content=valid_pdf(r.content)
   path=OUT/model/filename
   path.write_bytes(content)
   o.update(status="downloaded",size=len(content),sha256=hashlib.sha256(content).hexdigest(),response_url=r.url)
   print("OK",model,filename,len(content),flush=True)
   break
  except Exception as e:
   o["reason"]=repr(e)[:300]
   print("ERR",model,filename,attempt+1,o["reason"],flush=True)
   time.sleep(.5+attempt)
 return o
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:
 for r in concurrent.futures.as_completed([p.submit(retrieve,x) for x in CANDIDATES]):
  results.append(r.result())
# Restricted wayback network is attempted only once per article, with a small concurrency budget.
base="https://support.zortrax.com"
def fetch_archived(task):
 model,filename,slug=task
 origin=f"{base}/{slug}/"
 ret={"model":model,"filename":filename,"url":origin,"description":"Archived Zortrax illustrated step-by-step PDF","status":"failed"}
 page=f"https://web.archive.org/web/20261108000000id_/{origin}"
 try:
  r=requests.get(page,timeout=(7,17),headers=HEAD)
  r.raise_for_status()
  pdf_ids=list(dict.fromkeys(re.findall(r"pdf/create/steps\.php\?id=(\d+)",r.text)))
  if not pdf_ids: raise ValueError("No original PDF export id in archived support page")
  print("FOUND PDF IDS",slug,pdf_ids,flush=True)
  for pid in pdf_ids[:2]:
   pdfurl=f"{base}/pdf/create/steps.php?id={pid}"
   for ts in ("20261108000000","20230101000000"):
    mirror=f"https://web.archive.org/web/{ts}id_/{pdfurl}"
    try:
     p=requests.get(mirror,timeout=(7,19),headers=HEAD)
     p.raise_for_status()
     content=valid_pdf(p.content)
     (OUT/model/filename).write_bytes(content)
     ret.update(status="downloaded",url=mirror,original_pdf=pdfurl,size=len(content),sha256=hashlib.sha256(content).hexdigest())
     print("ARCHIVE PDF OK",model,filename,pid,len(content),flush=True)
     return ret
    except Exception as e:
     ret["reason"]=repr(e)[:200]
  raise ValueError(f"No valid PDF for ids {pdf_ids}")
 except Exception as e:
  ret["reason"]=repr(e)[:300]
  print("ARCHIVE FAILED",model,filename,ret["reason"],flush=True)
 return ret
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:
 for r in concurrent.futures.as_completed([p.submit(fetch_archived,x) for x in ORIGINAL_PAGES]):
  results.append(r.result())
result={"date":"2026-11-09","downloaded":[r for r in results if r["status"]=="downloaded"],"failed":[r for r in results if r["status"]=="failed"]}
(OUT/"DOWNLOAD_MANIFEST.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
lines=["DODATKOWE PLIKI ZORTRAX - WERYFIKACJA", "Oryginalne pliki PDF lub kopie wykonane przez serwisy instrukcji.","Nieudane pobrania NIE sa uznawane za pobrane dokumenty.",""]
for row in result["downloaded"]:lines.append(f"PDF: {row['model']}/{row['filename']} | {row['size']} bajtow | {row['url']}")
lines+=["","NIEUDANE POBRANIA - DO DALSZEGO SPRAWDZENIA:"]
for row in result["failed"]:lines.append(f"BRAK: {row['model']}/{row['filename']} | {row['url']} | {row.get('reason','')}")
(OUT/"RAPORT_POBRANIA.txt").write_text("\n".join(lines)+"\n",encoding="utf8")
print("RESULTS",len(result["downloaded"]),"downloaded",len(result["failed"]),"failed",flush=True)
