# -*- coding: utf-8 -*-
import json
import sys

sys.path.insert(0, "C:/Users/edics/Downloads/lotto-activo/lotto-activo/scraping")
import core
from scrapling import Fetcher

for slug in ("selva-plus", "guacharo-activo"):
    page = Fetcher.get("https://api.lotterly.co/v1/results/%s/" % slug,
                       headers={"User-Agent": core.UA}, timeout=90)
    raw = page.body.decode("utf-8", errors="replace")
    print("==", slug, page.status, len(raw), "bytes")
    datos = json.loads(raw)
    print("tipo:", type(datos).__name__)
    if isinstance(datos, dict):
        print("claves:", list(datos.keys())[:10])
        items = datos.get("results") or datos.get("data") or []
    else:
        items = datos
    print("items:", len(items))
    for it in items[:3]:
        print(json.dumps(it, ensure_ascii=False)[:400])
    with open("C:/Users/edics/Downloads/lotto-activo/lotto-activo/datos_multiloteria/crudos/arbitro_%s.json" % slug, "w", encoding="utf-8") as f:
        f.write(raw)
