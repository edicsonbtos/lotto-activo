# -*- coding: utf-8 -*-
"""Sondeo RD (desarrollo LA): ¿el operador evita pares consecutivos repetidos en la secuencia INTERCALADA LA h:00 / RD h:30?
Base = ag12 V1 (cross-fit). Para LA h:00 el predecesor intercalado es RD (h-1):30."""
import os, sys, csv, io
import numpy as np
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import arnes as A
WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WT, "herramientas"))
from rdint.datos import ANIMALES, sin_acentos, RD_CSV
import lotto_eval as LE
from datetime import date
D = A.datos().prefijo(A.CORTE)
P = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "P_V1.npy")); _, y = A.base()
rd = {}
for r in csv.DictReader(io.open(RD_CSV, encoding="utf-8")):
    c = ANIMALES.get(sin_acentos(r["animal"])); h = int(r["hora"][:2]) - 8
    if c is not None and r["hora"].endswith(":30") and 0 <= h <= 11: rd[(r["fecha"], h)] = LE.IDX[c]
# secuencia intercalada de eventos: (fecha, medio-hora, juego, animal)
ev = [(f, 2 * int(h), "LA", int(s), t) for t, (f, h, s) in enumerate(zip(D.fecha, D.hora, D.seq))]
ev += [(f, 2 * h + 1, "RD", s, -1) for (f, h), s in rd.items() if f <= D.fecha[-1]]
ev.sort()
jor = lambda f: (date.fromisoformat(f) - date(2023, 1, 1)).days
pares = defaultdict(list)   # (a,b) -> jornadas en que b siguió a a en la secuencia intercalada (mismo día)
tipo_pares = defaultdict(list)  # ((juegoA,juegoB),(a,b)) -> jornadas
res = defaultdict(lambda: [0, 0.0])
prev = None
for f, mh, g, s, t in ev:
    d = jor(f)
    if prev is not None and prev[0] == f and mh - prev[1] == 1:   # predecesor inmediato (30 min antes)
        a, ga = prev[3], prev[2]
        if g == "LA" and t >= A.W:
            j = t - A.W
            for nombre, dic, key in [("RD(h-1):30 -> LA, par visto en cualquier juego", pares, None),
                                     ("RD->LA, mismo par visto como RD->LA", tipo_pares, ("RD", "LA")),
                                     ("RD->LA, par visto como LA->RD", tipo_pares, ("LA", "RD"))]:
                for lo, hi in [(1, 1), (2, 7), (8, 30)]:
                    m = np.zeros(38, bool)
                    for b in range(38):
                        L = dic[(a, b)] if key is None else dic[(key, (a, b))]
                        if any(lo <= d - x <= hi for x in L): m[b] = True
                    if m.any(): res[(nombre, lo, hi)][0] += int(m[y[j]]); res[(nombre, lo, hi)][1] += P[j][m].sum()
            # control: el animal mismo de RD(h-1):30
            m = np.zeros(38, bool); m[a] = True
            res[("control: animal de RD(h-1):30", 0, 0)][0] += int(m[y[j]]); res[("control: animal de RD(h-1):30", 0, 0)][1] += P[j][m].sum()
        pares[(a, s)].append(d); tipo_pares[((ga, g), (a, s))].append(d)
    prev = (f, mh, g, s)
for k in sorted(res):
    o, e = res[k]
    print(f"{k[0]:48s} {k[1]:>2}-{k[2]:<2} obs {o:5d} esp {e:7.1f} O/E {o/e:5.3f} z {(o-e)/np.sqrt(e):+6.2f}")
