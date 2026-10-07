# -*- coding: utf-8 -*-
"""Baja de la fuente oficial (solo lectura) los sorteos posteriores al ultimo del archivo de historial local.
LA: 2026-09-16..hoy -> fresco_la.txt (formato del historial: fecha hora(0..11) codigo; solo filas nuevas).
RD Int (id 2): 2026-09-16..hoy -> fresco_rd.csv (fecha,hora0..11,codigo).
Contrasta con oficial_multi.csv y con el historial local donde se solapan. No escribe nada fuera de esta carpeta."""
import os, sys, csv, datetime as dt
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "scraping")); import fuente_oficial as F
HOY = dt.date(2026, 10, 7)
la, rd = {}, {}
d = dt.date(2026, 9, 16)
while d <= HOY:
    f = d.isoformat()
    js = F._pedir(f, F.token())
    for juego in js.get("datos") or []:
        gid = str(juego.get("id"))
        if gid not in ("1", "2"):
            continue
        for r in juego.get("resultados") or []:
            hs = str(r.get("time_s", "")).strip().lstrip("0")
            cod, _ = F.codigo_de(r.get("number_animal"), r.get("name_animal"))
            if not cod:
                continue
            if gid == "1" and hs in F.HORAS:
                la[(f, F.HORAS.index(hs))] = cod
            if gid == "2":
                hh = int(hs.split(":")[0]); ap = hs.split()[-1]
                h24 = hh % 12 + (12 if ap == "PM" else 0); rd[(f, h24 - 8)] = cod
    print(f, sum(k[0] == f for k in la), sum(k[0] == f for k in rd), flush=True)
    d += dt.timedelta(days=1)
with open(os.path.join(AQUI, "fresco_la.txt"), "w", encoding="utf-8") as fh:
    for (f, h), c in sorted(la.items()):
        if (f, h) > ("2026-09-16", 7):
            fh.write(f"{f} {h} {c}\n")
with open(os.path.join(AQUI, "fresco_rd.csv"), "w", encoding="utf-8") as fh:
    fh.write("fecha,hora,codigo\n")
    for (f, h), c in sorted(rd.items()):
        fh.write(f"{f},{h},{c}\n")
HOR = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
ofi = {}
with open(os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["juego"] == "1" and r["hora"] in HOR:
            ofi[(r["fecha"], HOR.index(r["hora"]))] = r["codigo"]
loc = {}
for ln in open(os.path.join(RAIZ, "historial" + ".txt"), encoding="utf-8"):
    p = ln.split()
    if len(p) == 3:
        loc[(p[0], int(p[1]))] = p[2]
print("LA vs oficial_multi:", sum((k in ofi) for k in la), "contrastadas;", [k for k in la if k in ofi and ofi[k] != la[k]], "discrepancias")
print("LA vs historial local:", sum((k in loc) for k in la), "contrastadas;", [k for k in la if k in loc and loc[k] != la[k]], "discrepancias")
print("LA nuevas:", sum(1 for k in la if k > ("2026-09-16", 7)), " RD:", len(rd))
