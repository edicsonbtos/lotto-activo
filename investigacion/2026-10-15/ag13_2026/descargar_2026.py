# -*- coding: utf-8 -*-
"""Baja el archivo por fecha de lotoven y loteriadehoy para 2026-01-01..2026-09-14 (anexo 1 del preregistro ag13).
Reutiliza los parsers de pronosticadores/descargar.py. Reanudable. Salida: ag13_2026/publicados_2026.jsonl."""
import json, os, sys, time
from datetime import date, timedelta
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "pronosticadores"))
import descargar as D
SAL = os.path.join(AQUI, "publicados_2026.jsonl")
hechos = set()
if os.path.exists(SAL):
    for ln in open(SAL, encoding="utf-8"):
        r = json.loads(ln)
        if "error" not in r["datos"]:
            hechos.add((r["fuente"], r["fecha"]))
d, fin = date(2026, 1, 1), date(2026, 9, 14)
with open(SAL, "a", encoding="utf-8") as fo:
    while d <= fin:
        f = d.isoformat()
        for fuente, url in D.URL.items():
            if (fuente, f) in hechos:
                continue
            res = {"error": "sin intentar"}
            for _ in range(3):
                try:
                    h = D.bajar(url, f)
                    if len(h) < 2000:
                        raise OSError("página corta")
                    res = (D.p_lotoven if fuente == "lotoven" else D.p_ldh)(h, f); break
                except Exception as ex:  # noqa: BLE001
                    res = {"error": repr(ex)[:100]}; time.sleep(5)
            fo.write(json.dumps({"fuente": fuente, "fecha": f, "datos": res}, ensure_ascii=False) + "\n"); fo.flush()
            time.sleep(0.7)
        print(f, flush=True); d += timedelta(days=1)
print("LISTO", flush=True)
