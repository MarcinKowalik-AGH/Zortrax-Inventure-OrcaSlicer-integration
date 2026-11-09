#!/usr/bin/env python3
"""Download official Zortrax illustrated disassembly/reassembly procedures to a ZIP artifact."""
import concurrent.futures
import gzip
import hashlib
import json
import random
import re
import time
import requests
from pathlib import Path

BASE = "https://support.zortrax.com"
# (output PDF filename, manufacturer page slug, manufacturer PDF-button ID, category)
MANUALS = {
"M300": [
 ("01_Wymiana_hotendu.pdf","hotend-replacement",10238,"Glowica i ekstruder"),
 ("02_Wymiana_dyszy.pdf","nozzle-replacement",9984,"Glowica i ekstruder"),
 ("03_Wymiana_grzalki_i_termopary.pdf","thermocoupler-and-heater-replacement",10172,"Glowica i ekstruder"),
 ("04_Wymiana_lozyska_ekstrudera.pdf","extruder-bearing-replacement",8258,"Glowica i ekstruder"),
 ("05_Wymiana_silnika_ekstrudera.pdf","extruder-motor-replacement",12551,"Glowica i ekstruder"),
 ("06_Rozbiorka_bloku_aluminiowego_ekstrudera.pdf","extruder-aluminum-block-replacement",13451,"Rozbiorka i montaz"),
 ("07_Konserwacja_silnika_ekstrudera.pdf","extruder-motor-maintenance",9658,"Glowica i ekstruder"),
 ("08_Wymiana_plytki_PCB_ekstrudera.pdf","m-series-extruder-pcb-replacement",9402,"Elektronika"),
 ("09_Wymiana_wentylatorow_ekstrudera.pdf","extruder-fans-replacement",11704,"Chlodzenie"),
 ("10_Wymiana_wentylatora_dolnego.pdf","m-series-bottom-fan-replacement",8170,"Chlodzenie"),
 ("11_Wymiana_wiazki_ekstrudera.pdf","extruder-cable-replacement",10597,"Okablowanie"),
 ("12_Wymiana_silnika_osi_Z.pdf","z-axis-motor-replacement",10932,"Mechanika"),
 ("13_Wymiana_sprzegla_osi_Z.pdf","z-axis-coupler-replacement",11085,"Mechanika"),
 ("14_Wymiana_paskow_napedowych.pdf","belts-replacement",19814,"Mechanika"),
 ("15_Regulacja_i_demontaz_osi_M300.pdf","m300-axes-maintenance",13547,"Mechanika"),
 ("16_Regulacja_osi_M300_przyrzady.pdf","m300-axes-maintenance-with-jigs",14496,"Mechanika"),
 ("17_Wymiana_krancowek.pdf","endstop-replacement",9418,"Czujniki"),
 ("18_Wymiana_panelu_wyswietlacza.pdf","m-series-display-panel-replacement",8319,"Panel"),
 ("19_Wymiana_wlacznika_zasilania.pdf","power-switch-replacement",8564,"Zasilanie"),
 ("20_Wymiana_bezpiecznika.pdf","fuse-replacement",8114,"Zasilanie"),
 ("21_Wymiana_zasilacza.pdf","power-supply-unit-replacement",12213,"Zasilanie"),
 ],
"M300_Dual":[
 ("01_Rozbiorka_i_skladanie_ekstrudera.pdf","extruder-maintenance",27120,"Rozbiorka i montaz"),
 ("02_Regulacja_i_demontaz_osi.pdf","axes-maintenance-m300-dual",30823,"Mechanika"),
 ("03_Konserwacja_calej_drukarki.pdf","m300-dual-maintenance-guide",27014,"Konserwacja"),
 ],
"Inventure":[
 ("01_Wymiana_kompletnego_ekstrudera.pdf","extruder-replacement",15818,"Rozbiorka i montaz"),
 ("02_Wymiana_modulu_hotendu.pdf","hotend-module-replacement",15379,"Glowica i ekstruder"),
 ("03_Wymiana_wiazki_ekstrudera.pdf","inventure-extruder-cable-replacement",17672,"Okablowanie"),
 ("04_Wymiana_gornego_wentylatora_ekstrudera.pdf","extruder-upper-fan-replacement",16918,"Chlodzenie"),
 ("05_Wymiana_filtra_HEPA.pdf","hepa-filter-replacement",16251,"Filtracja"),
 ("06_Wymiana_dyszy.pdf","inventure-nozzle-replacement",16254,"Glowica i ekstruder"),
 ("07_Wymiana_wiazki_platformy.pdf","inventure-platform-cable-replacement",17868,"Okablowanie"),
 ("08_Wymiana_szczotek_pojemnika_na_odpady.pdf","waste-container-brushes-replacement",15867,"Czyszczenie i serwis"),
 ("09_Konserwacja_calej_drukarki.pdf","inventure-maintenance-guide",16982,"Konserwacja"),
 ]
}
# Prioritize limited online archive access for the models with no offline repair PDFs.
MANUALS = {model: MANUALS[model] for model in ("Inventure","M300_Dual","M300")}
ROOT=Path("service_downloads"); ROOT.mkdir(exist_ok=True)
for model in MANUALS: (ROOT/model).mkdir(parents=True,exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125 Safari/537.36","Accept":"application/pdf,*/*","Accept-Encoding":"gzip, deflate"}
def get(args):
  model,item=args
  name,slug,pdfid,category=item
  official=f"{BASE}/{slug}/"
  pdfurl=f"{BASE}/pdf/create/steps.php?id={pdfid}"
  candidates=[
   f"https://web.archive.org/web/20261108000000id_/{pdfurl}",
   f"https://web.archive.org/web/20240101000000id_/{pdfurl}",
   # Some archived snapshots use a direct archived filename instead of generated endpoint.
  ]
  failures=[]
  for url in candidates:
    for attempt in range(2):
      try:
        res=requests.get(url,headers=HEADERS,timeout=(12,36),allow_redirects=True)
        res.raise_for_status()
        payload=res.content
        if payload.startswith(b"\x1f\x8b"): payload=gzip.decompress(payload)
        if payload[:5]!=b"%PDF-" or len(payload)<12000:
          raise ValueError(f"not a PDF ({len(payload)} bytes, {payload[:24]!r})")
        outfile=ROOT/model/name
        outfile.write_bytes(payload)
        meta={"name":name,"category":category,"model":model,"source_article":official,"original_pdf_url":pdfurl,"archive_pdf_url":url,"pdf_bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest()}
        print(f"OK {model}/{name} {len(payload)} bytes",flush=True)
        return model,meta,None
      except Exception as error:
        err=f"{type(error).__name__}: {str(error)[:150]}"
        failures.append(f"{url} {err}")
        print(f"RETRY {model}/{name}: {err}",flush=True)
        time.sleep(1.5+attempt*2.0)
  print(f"MISSING {model}/{name}",flush=True)
  return model,None,{"name":name,"category":category,"model":model,"source_article":official,"original_pdf_url":pdfurl,"failed_reasons":failures}
results={m:{"downloaded":[],"unavailable":[]} for m in MANUALS}
tasks=[(model,item) for model,docs in MANUALS.items() for item in docs]
# Limit automated Wayback requests to mitigate rate limiting.
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  fs=[ex.submit(get,x) for x in tasks]
  for future in concurrent.futures.as_completed(fs):
    model,meta,error=future.result()
    if meta: results[model]["downloaded"].append(meta)
    else: results[model]["unavailable"].append(error)
for model,data in results.items():
  data["downloaded"].sort(key=lambda x:x["name"])
  data["unavailable"].sort(key=lambda x:x["name"])
  (ROOT/model/"manifest_serwis.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf8")
  lines=["OFFICIAL ZORTRAX STEP-BY-STEP REPAIR GUIDES",f"MODEL: {model}","","Downloaded original Zortrax illustrated PDF manuals from archival snapshots.","", "AVAILABLE OFFLINE:"]
  lines.extend(f"- {x['name']} | {x['source_article']}" for x in data["downloaded"])
  lines += ["","OFFLINE PDF NOT AVAILABLE - ORIGINAL ARTICLE LINKS:"]
  lines.extend(f"- {x['name']} | {x['source_article']} | {x['original_pdf_url']}" for x in data["unavailable"])
  (ROOT/model/"LINKI_DO_PROCEDUR_SERWISOWYCH.txt").write_text("\n".join(lines)+"\n",encoding="utf8")
  print(f"TOTAL {model} pdf={len(data['downloaded'])} links_only={len(data['unavailable'])}",flush=True)
(ROOT/"PODSUMOWANIE_SERWIS.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf8")
