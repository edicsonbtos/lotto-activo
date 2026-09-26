# -*- coding: utf-8 -*-
"""Sondeo 2 (desarrollo): residuo frente a ag12 V1 de otras formas de 'no repetir un patrón reciente'."""
import os, sys
import numpy as np
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import arnes as A
D = A.datos().prefijo(A.CORTE)
P = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "P_V1.npy")); _, y = A.base()
seq = np.asarray(D.seq); hora = np.asarray(D.hora); _, dn = np.unique(np.asarray(D.dia), return_inverse=True)
n = len(seq); W = A.W
res = defaultdict(lambda: [0, 0.0])
def add(key, m, j):
    if m.any(): res[key][0] += int(m[y[j]]); res[key][1] += P[j][m].sum()
porhora = defaultdict(list)   # hora -> [(jornada, animal)]
porpos = defaultdict(list)    # k -> [(jornada, animal)]
tri = defaultdict(list)       # (a,b) -> [(jornada, c)]
cruce = defaultdict(list)     # último de ayer a -> [(jornada, primero)]
primeros = []                 # (jornada, animal) primer sorteo
kpos = np.zeros(n, int)
for t in range(1, n):
    kpos[t] = kpos[t-1] + 1 if dn[t] == dn[t-1] else 0
for t in range(n):
    d = dn[t]; k = kpos[t]
    if t >= W:
        j = t - W
        for lo, hi in [(1, 1), (2, 7), (8, 30)]:
            m = np.zeros(38, bool)
            for jd, a in porhora[hora[t]]:
                if lo <= d - jd <= hi: m[a] = True
            add(("misma hora", lo, hi), m, j)
            m = np.zeros(38, bool)
            for jd, a in porpos[k]:
                if lo <= d - jd <= hi: m[a] = True
            add(("misma posición k", lo, hi), m, j)
            if k >= 2:
                m = np.zeros(38, bool)
                for jd, c in tri[(seq[t-2], seq[t-1])]:
                    if lo <= d - jd <= hi * 3: m[c] = True
                add(("trío s2,s1->i", lo, hi * 3), m, j)
            if k == 0 and t >= 1:
                m = np.zeros(38, bool)
                for jd, c in cruce[seq[t-1]]:
                    if lo <= d - jd <= hi: m[c] = True
                add(("cruce ayer->hoy", lo, hi), m, j)
                m = np.zeros(38, bool)
                for jd, a in primeros:
                    if lo <= d - jd <= hi: m[a] = True
                add(("primero del día", lo, hi), m, j)
    porhora[hora[t]].append((d, seq[t])); porpos[k].append((d, seq[t]))
    if k >= 2: tri[(seq[t-2], seq[t-1])].append((d, seq[t]))
    if k == 0:
        primeros.append((d, seq[t]))
        if t >= 1: cruce[seq[t-1]].append((d, seq[t]))
    # poda
    for L in (porhora[hora[t]], porpos[k]):
        while L and d - L[0][0] > 30: L.pop(0)
    while primeros and d - primeros[0][0] > 30: primeros.pop(0)
for kk in sorted(res):
    o, e = res[kk]
    print(f"{kk[0]:20s} hace {kk[1]:>2}-{kk[2]:<3} obs {o:5d} esp {e:7.1f} O/E {o/e:5.3f} z {(o-e)/np.sqrt(e):+6.2f}")
