# -*- coding: utf-8 -*-
"""Sondeo crudo (desarrollo): O/E frente al ensamble de variantes del mecanismo 'evitar transición repetida'."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import arnes as A
D = A.datos().prefijo(A.CORTE)
P, y = A.base(); P = P / P.sum(1, keepdims=True)
seq = np.asarray(D.seq); dia = np.asarray(D.dia); hora = np.asarray(D.hora)
_, dnum = np.unique(dia, return_inverse=True)   # índice de jornada
n = len(seq); W = A.W
VENT = [(0, 0), (1, 1), (2, 7), (8, 30), (31, 90)]   # antigüedad en días
from collections import defaultdict
tr = defaultdict(list)   # (a,b) -> jornadas en que b siguió a a (dentro del día)
tr2 = defaultdict(list)  # (a,b) -> b salió 2 sorteos después de a (mismo día)
res = defaultdict(lambda: [0, 0.0])
def add(key, mask_i, j):
    res[key][0] += int(mask_i[y[j]]); res[key][1] += P[j][mask_i].sum()
for t in range(n):
    if t >= W:
        j = t - W; d = dnum[t]
        s1 = seq[t-1] if dnum[t-1] == d else None
        s2 = seq[t-2] if t >= 2 and dnum[t-2] == d else None
        if s1 is not None:
            for nombre, dic, a in [("s1->i", tr, s1), ("i->s1 (inversa)", None, s1), ("s2->?->i", tr2, s2)]:
                if a is None: continue
                for lo, hi in VENT:
                    m = np.zeros(38, bool)
                    if dic is not None:
                        for b in range(38):
                            if any(lo <= d - x <= hi for x in dic.get((a, b), ())): m[b] = True
                    else:
                        for b in range(38):
                            if any(lo <= d - x <= hi for x in tr.get((b, a), ())): m[b] = True
                    m[a] = False
                    add((nombre, lo, hi), m, j)
            # s2->i (salto) directo como transición normal
            if s2 is not None:
                for lo, hi in VENT:
                    m = np.zeros(38, bool)
                    for b in range(38):
                        if any(lo <= d - x <= hi for x in tr.get((s2, b), ())): m[b] = True
                    add(("s2->i como transición", lo, hi), m, j)
    if t >= 1 and dnum[t-1] == dnum[t]:
        tr[(seq[t-1], seq[t])].append(dnum[t])
    if t >= 2 and dnum[t-2] == dnum[t]:
        tr2[(seq[t-2], seq[t])].append(dnum[t])
for k in sorted(res):
    o, e = res[k]
    if e > 0: print(f"{k[0]:24s} hace {k[1]:>2}-{k[2]:<2} días  obs {o:5d}  esp {e:7.1f}  O/E {o/e:5.3f}  z {(o-e)/np.sqrt(e):+6.2f}")
