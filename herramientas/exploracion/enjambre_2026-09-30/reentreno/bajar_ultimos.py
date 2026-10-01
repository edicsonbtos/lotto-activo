# -*- coding: utf-8 -*-
"""Baja de la API oficial los dias 2026-09-23..2026-09-29 (juegos 1 y 2) a oficial_extra.csv (solo esta carpeta)."""
import csv, io, os, sys, time
from datetime import date, timedelta
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas", "lard"))
import descargar as DG
F = DG.F
out = []
d = date(2026, 9, 23)
while d <= date(2026, 9, 29):
    f = d.isoformat()
    for i in range(3):
        try:
            out += [r for r in DG.filas_dia(F._pedir(f, F.token(refrescar=i > 0)), f) if r[1] in ("1", "2")]
            break
        except Exception as e:
            print(f, "fallo", e); time.sleep(3)
    time.sleep(0.3); d += timedelta(days=1)
with io.open(os.path.join(AQUI, "oficial_extra.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh); w.writerow(["fecha", "juego", "hora", "codigo"]); w.writerows(out)
print(len(out), "filas")
