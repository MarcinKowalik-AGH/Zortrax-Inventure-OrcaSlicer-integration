#!/usr/bin/env python3
"""Prepare official Zortrax PDF documentation archives; run only in isolated CI branch."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request

BASE="https://support.zortrax.com"
DOCUMENTS={
 "M300":[
   ("M300_User_Guide_PL_2018.pdf",f"{BASE}/wp-content/uploads/2020/11/instrukcja_obslugi_zortrax_seriam_26082018.pdf"),
   ("M300_User_Guide_EN_2018.pdf",f"{BASE}/wp-content/uploads/2020/11/user_guide_zortrax_mseries_26082018.pdf"),
 ],
 "M300_Dual":[
   ("M300_Dual_User_Guide_PL_2025.pdf",f"{BASE}/wp-content/uploads/2025/08/instrukcja_obslugi_zortrax_m300_dual_01082025.pdf"),
   ("M300_Dual_User_Guide_EN_2025.pdf",f"{BASE}/wp-content/uploads/2025/08/user_guide_zortrax_m300_dual_01082025.pdf"),
   ("M300_Dual_User_Guide_PL_2020.pdf",f"{BASE}/wp-content/uploads/2020/11/instrukcja_obslugi_zortrax_m300_dual_14102020.pdf"),
 ],
 "Inventure":[
   ("Inventure_User_Guide_PL_2020.pdf",f"{BASE}/wp-content/uploads/2020/11/instrukcja_obslugi_inventure_14102020.pdf"),
   ("Inventure_User_Guide_EN_2020.pdf",f"{BASE}/wp-content/uploads/2020/11/user_guide_zortrax_inventure_14102020.pdf"),
   ("Inventure_User_Guide_EN_2021.pdf",f"{BASE}/wp-content/uploads/2022/01/user_guide_zortrax_inventure_2021.03.12.pdf"),
 ]
}
PAGES={
 "M300":[
  ("Rozpakowanie_i_pierwsze_uruchomienie", "m300-unpacking-first-use"),
  ("Konserwacja", "m300-maintenance-guide"),
  ("Pakowanie_do_transportu", "m300-packing"),
 ],
 "M300_Dual":[
  ("Rozpakowanie_i_uruchomienie", "m300-dual-unpacking-setting-up"),
  ("Konserwacja", "m300-dual-maintenance-guide"),
  ("Pakowanie_do_transportu", "m300-dual-packing"),
 ],
 "Inventure":[
  ("Rozpakowanie_i_pierwsze_uruchomienie", "inventure-unpacking-first-use"),
  ("Poziomowanie_platformy", "inventure-platform-leveling"),
  ("Konserwacja", "inventure-maintenance-guide"),
  ("Kalibracja_dysz", "inventure-nozzle-alignment-calibration"),
 ],
}
head={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) ZortraxDocumentationArchive/1.0",
      "Accept":"application/pdf,text/html;q=0.9,*/*;q=0.8"}
root=Path("build")
root.mkdir(exist_ok=True)
report={}
for model,docs in DOCUMENTS.items():
 dest=root/model
 dest.mkdir(exist_ok=True)
 manifest={"printer":model,"original_pdf_files":[],"converted_support_pages":[],"failed":[]}
 for name,url in docs:
  content=None
  for attempt in range(3):
   try:
    req=urllib.request.Request(url,headers=head)
    with urllib.request.urlopen(req, timeout=65) as res:
     content=res.read()
    if content[:5]!=b"%PDF-":
     raise ValueError("Response is not a PDF")
    if len(content)<20000:
     raise ValueError("PDF smaller than 20 KB")
    (dest/name).write_bytes(content)
    manifest["original_pdf_files"].append({"name":name,"source":url,"bytes":len(content),"sha256":hashlib.sha256(content).hexdigest()})
    print(f"OK {model}/{name}: {len(content):,}")
    break
   except Exception as e:
    print(f"RETRY {model}/{name} {attempt+1}: {e}",flush=True)
    if attempt==2:
     manifest["failed"].append({"file":name,"url":url,"reason":str(e)})
    time.sleep(attempt+1)
 report[model]=manifest
# Render the chosen official knowledge-base articles to PDF (not original Zortrax PDF files).
chrome=next((p for p in ("google-chrome","chromium","chromium-browser") if shutil.which(p)),None)
if chrome:
 for model,steps in PAGES.items():
  dest=root/model
  for title,slug in steps:
   url=f"{BASE}/{slug}/"
   output=dest/("Support_"+title+".pdf")
   with tempfile.TemporaryDirectory() as temp:
    args=[chrome,"--headless","--disable-gpu","--no-sandbox","--disable-dev-shm-usage",
         "--hide-scrollbars","--virtual-time-budget=12000",f"--user-data-dir={temp}",
         "--no-pdf-header-footer",f"--print-to-pdf={output.absolute()}",url]
    try:
     r=subprocess.run(args,capture_output=True,text=True,timeout=85)
     if r.returncode or not output.exists() or output.stat().st_size<15000 or output.open("rb").read(5)!=b"%PDF-":
      raise RuntimeError((r.stderr or r.stdout)[-300:])
     report[model]["converted_support_pages"].append({"name":output.name,"source":url,"bytes":output.stat().st_size})
     print(f"PRINT OK {model}/{title}: {output.stat().st_size:,}")
    except Exception as e:
     output.unlink(missing_ok=True)
     report[model]["failed"].append({"page":title,"url":url,"reason":str(e)})
     print(f"PRINT FAILED {model}/{title}: {e}")
else: print("Chrome not available; support links are in README.")
for model,manifest in report.items():
 dest=root/model
 intro=[
 f"ZORTRAX {model}: zestaw instrukcji PDF",
 "Data przygotowania: 2026-11-09.",
 "Pliki User_Guide to oryginalne pliki PDF producenta, bez zmian.",
 "Pliki Support_ to kopie stron pomocy Zortrax wydrukowane do PDF przez przegladarke, nie oficjalne wydania PDF.",
 "Uwaga: M300 oznacza klasyczna drukarke Zortrax M300, NIE M300 Plus.",
 "",
 "Oryginalne pliki:",
 ]
 intro += [f" - {m['name']} | {m['source']}" for m in manifest["original_pdf_files"]]
 intro += ["","Strony pomocy PDF (konwersja HTML):"]
 intro += [f" - {m['name']} | {m['source']}" for m in manifest["converted_support_pages"]]
 intro += ["","Dodatkowe procedury na oficjalnej stronie: ",
           f"  {BASE}/all-categories/?printers={model.lower().replace('_','-')}",
           f"  {BASE}/user-guides/",
           "","Nieudane pobrania / brak plikow:"]
 intro += [f" - {m.get('file',m.get('page'))} | {m['url']} | {m['reason']}" for m in manifest["failed"]]
 (dest/"INDEKS.txt").write_text("\n".join(intro)+"\n",encoding="utf-8")
 (dest/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
(root/"PODSUMOWANIE.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("FINAL:",json.dumps({m:{"originals":len(v["original_pdf_files"]),"printouts":len(v["converted_support_pages"]),"failed":len(v["failed"])} for m,v in report.items()}))
if any(not v["original_pdf_files"] for v in report.values()):
 raise SystemExit("ERROR: At least one printer has zero official PDF manuals")
