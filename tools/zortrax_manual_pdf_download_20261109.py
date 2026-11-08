#!/usr/bin/env python3
"""Collect independently downloadable Zortrax manuals and official support PDFs."""
import concurrent.futures
import hashlib
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = "https://support.zortrax.com"
DOCS = {
    "M300": [
        ("Instrukcja_M300_M-Series_PL_2018.pdf",f"{BASE}/wp-content/uploads/2020/11/instrukcja_obslugi_zortrax_seriam_26082018.pdf","podrecznik producenta"),
        ("Instrukcja_M300_M-Series_EN_2018.pdf",f"{BASE}/wp-content/uploads/2020/11/user_guide_zortrax_mseries_26082018.pdf","podrecznik producenta"),
        ("Serwis_M300_Pierwsze_uruchomienie_EN.pdf",f"{BASE}/pdf/create/steps.php?id=10728","PDF z bazy wiedzy producenta"),
        ("Serwis_M300_Konserwacja_EN.pdf",f"{BASE}/pdf/create/steps.php?id=10836","PDF z bazy wiedzy producenta"),
    ],
    "M300_Dual": [
        ("Instrukcja_M300_Dual_PL_2025.pdf",f"{BASE}/wp-content/uploads/2025/08/instrukcja_obslugi_zortrax_m300_dual_01082025.pdf","podrecznik producenta"),
        ("Instrukcja_M300_Dual_EN_2025.pdf",f"{BASE}/wp-content/uploads/2025/08/user_guide_zortrax_m300_dual_01082025.pdf","podrecznik producenta"),
        ("Instrukcja_M300_Dual_PL_2020.pdf",f"{BASE}/wp-content/uploads/2020/11/instrukcja_obslugi_zortrax_m300_dual_14102020.pdf","podrecznik producenta"),
        ("M300_Dual_Instrukcja_PL_Botland_2019.pdf","https://botland.com.pl/index.php?controller=attachment&id_attachment=3258","Instrukcja producenta z archiwum sklepu Botland"),
        ("M300_Dual_Specyfikacja_Botland.pdf","https://botland.com.pl/index.php?controller=attachment&id_attachment=3257","Karta produktu z archiwum sklepu Botland"),
        ("M300_Dual_Opis_Botland.pdf","https://botland.com.pl/index.php?controller=attachment&id_attachment=3256","Opis produktu z archiwum sklepu Botland"),
        ("Serwis_M300_Dual_Konserwacja_EN.pdf",f"{BASE}/pdf/create/steps.php?id=27014","PDF z bazy wiedzy producenta"),
    ],
    "Inventure": [
        ("Instrukcja_Inventure_PL_2020.pdf",f"{BASE}/wp-content/uploads/2020/11/instrukcja_obslugi_inventure_14102020.pdf","podrecznik producenta"),
        ("Instrukcja_Inventure_EN_2020.pdf",f"{BASE}/wp-content/uploads/2020/11/user_guide_zortrax_inventure_14102020.pdf","podrecznik producenta"),
        ("Instrukcja_Inventure_EN_2021.pdf",f"{BASE}/wp-content/uploads/2022/01/user_guide_zortrax_inventure_2021.03.12.pdf","podrecznik producenta"),
        ("Serwis_Inventure_Konserwacja_EN.pdf",f"{BASE}/pdf/create/steps.php?id=16982","PDF z bazy wiedzy producenta"),
    ],
}
SUPPORT_LINKS={
    "M300":["https://support.zortrax.com/m300-unpacking-first-use/","https://support.zortrax.com/m300-maintenance-guide/","https://support.zortrax.com/m300-packing/"],
    "M300_Dual":["https://support.zortrax.com/m300-dual-unpacking-setting-up/","https://support.zortrax.com/m300-dual-maintenance-guide/","https://support.zortrax.com/m300-dual-packing/"],
    "Inventure":["https://support.zortrax.com/inventure-unpacking-first-use/","https://support.zortrax.com/inventure-platform-leveling/","https://support.zortrax.com/inventure-maintenance-guide/","https://support.zortrax.com/nozzle-alignment-calibration/"],
}
ROOT=Path("build")
ROOT.mkdir(exist_ok=True)
for model in DOCS: (ROOT/model).mkdir(exist_ok=True)
TASKS=[(model,*item) for model,items in DOCS.items() for item in items]
HEADERS={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15", "Accept":"application/pdf,application/octet-stream;q=0.9,*/*;q=0.5"}
def fetch(task):
    model,name,url,kind=task
    if url.startswith(BASE):
        alternatives=[
            f"https://web.archive.org/web/20261108000000id_/{url}",
            f"https://web.archive.org/web/20230101000000id_/{url}",
        ]
    else:
        alternatives=[url]
    last="not attempted"
    for candidate in alternatives:
        try:
            request=urllib.request.Request(candidate,headers=HEADERS)
            with urllib.request.urlopen(request,timeout=38) as r:
                payload=r.read(35_000_000)
            if not payload.startswith(b"%PDF-") or len(payload)<18000:
                raise ValueError(f"Expected PDF, got {len(payload)} bytes and {payload[:24]!r}")
            target=ROOT/model/name
            target.write_bytes(payload)
            result={"file":name,"source":candidate,"original_url":url,"type":kind,"size":len(payload),"sha256":hashlib.sha256(payload).hexdigest()}
            print("OK",model,name,len(payload),"FROM",candidate,flush=True)
            return model,result,None
        except Exception as error:
            last=f"{type(error).__name__}: {error}"
            print("FAILED",model,name,candidate,last,flush=True)
    return model,None,{"file":name,"source":url,"reason":last}
report={k:{"model":k,"downloaded":[],"failed":[],"additional_official_guides":SUPPORT_LINKS[k]} for k in DOCS}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    for future in concurrent.futures.as_completed([pool.submit(fetch,t) for t in TASKS]):
        model,ok,error=future.result()
        if ok: report[model]["downloaded"].append(ok)
        if error:report[model]["failed"].append(error)
for model,item in report.items():
    folder=ROOT/model
    item["downloaded"].sort(key=lambda x:x["file"])
    title=f"Dokumentacja Zortrax {model.replace('_',' ')}\n"
    title+=("Oryginalne instrukcje producenta i oficjalne PDF z bazy wiedzy.\n"
           "M300 oznacza model klasyczny; nie M300 Plus.\n\n"
           "PL - polska wersja; EN - angielska wersja.\n\nZawartosc:\n")
    for x in item["downloaded"]:
        title+=f"- {x['file']}\n  {x['source']}\n"
    title+="\nDodatkowe instrukcje w witrynie producenta (niekoniecznie dolaczone jako PDF):\n"
    for url in item["additional_official_guides"]:title+=f"- {url}\n"
    if item["failed"]:
        title+="\nPliki, ktorych nie udalo sie pobrac:\n"
        for x in item["failed"]:title+=f"- {x['file']} : {x['source']}\n"
    (folder/"SPIS_PLIKOW_I_ZRODEL.txt").write_text(title,encoding="utf-8")
    (folder/"manifest.json").write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding="utf-8")
(ROOT/"PODSUMOWANIE.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("PODSUMOWANIE:",json.dumps({k:{"pdf":len(v["downloaded"]),"errors":len(v["failed"])} for k,v in report.items()}),flush=True)
if any(not x["downloaded"] for x in report.values()):raise SystemExit("At least one printer is missing all documents")
