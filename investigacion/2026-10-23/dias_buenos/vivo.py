# -*- coding: utf-8 -*-
"""Vivo (pronósticos congelados del ensamble, /api/mesa): aciertos Top-15 por día y qué salió cada día."""
import os, json, glob, csv
from collections import defaultdict
from datetime import date
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RAW = os.path.join(RAIZ, "investigacion/2026-10-23/enjambre_semanal/ag4_semana_actual/raw/la")
filas = {}
for f in glob.glob(os.path.join(RAW, "*.json*")):
    try: d = json.load(open(f))
    except Exception: continue
    if d.get("winner_rank") is None: continue
    filas[(d["fecha"], int(d["hora"]))] = d
ult, gap = {}, {}
for r in sorted((r for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/oficial_multi.csv"))) if r["juego"] == "1"),
                key=lambda r: (r["fecha"], r["hora"])):
    dd = date.fromisoformat(r["fecha"]).toordinal(); co = r["codigo"]
    gap[(r["fecha"], int(r["hora"][:2]) - 8)] = (dd - ult[co]) if co in ult else 99
    ult[co] = dd
dias = defaultdict(list)
for k in sorted(filas): dias[k[0]].append((k[1], filas[k]))
DS = "lun mar mié jue vie sáb dom".split()
print(f"sorteos en vivo: {len(filas)}, días: {len(dias)}  (ensamble congelado antes de cada sorteo)")
print(f"\n{'fecha':11s}{'día':4s}{'Top15':>7s}{'modelo':>7s}{'Top5':>5s}  ganadores: número(puesto en la lista · días sin salir; R = ya había salido hoy)")
tot = defaultdict(lambda: [0, 0, 0.0]); cat = defaultdict(lambda: [0, 0])
for fe in sorted(dias):
    ds = dias[fe]
    h15 = sum(d["winner_rank"] <= 15 for _, d in ds); h5 = sum(d["winner_rank"] <= 5 for _, d in ds)
    esp = sum(sum(sorted((a["prob"] for a in d["animales"]), reverse=True)[:15]) for _, d in ds)
    w = DS[date.fromisoformat(fe).weekday()]
    t = tot[w]; t[0] += h15; t[1] += len(ds); t[2] += esp
    partes = []
    for h, d in ds:
        g = gap.get((fe, h))
        c = "?" if g is None else ("R" if g == 0 else ("1-2d" if g <= 2 else ("3-5d" if g <= 5 else ">5d")))
        cat[c][0] += d["winner_rank"] <= 15; cat[c][1] += 1
        partes.append(f"{d['winner_num']}({d['winner_rank']}·{'R' if g == 0 else (str(g)+'d' if g is not None else '?')})")
    print(f"{fe:11s}{w:4s}{h15:4d}/{len(ds):<3d}{esp:6.1f}{h5:5d}  " + " ".join(partes))
print("\nPor día de semana:", "  ".join(f"{w} {v[0]}/{v[1]}={v[0]/v[1]:.0%} (modelo {v[2]/v[1]:.0%})" for w, v in tot.items()))
print("Acierto Top-15 según el hueco del ganador:", "  ".join(f"{k}: {v[0]}/{v[1]}={v[0]/max(v[1],1):.0%}" for k, v in sorted(cat.items())))
