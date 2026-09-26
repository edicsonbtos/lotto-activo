# -*- coding: utf-8 -*-
"""DIAGNÓSTICO POSTERIOR (no cambia el veredicto): O/E de s1->i repetido (2-7 jornadas) frente al ensamble, por año, en el sellado."""
import os, sys
import numpy as np
from collections import defaultdict
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "herramientas"))
import lotto_eval as LE
D = LE.cargar(os.path.join(AQUI, "sellado_la.txt")); P = np.load(os.path.join(AQUI, "P_ens_sellado.npy"))
seq = D.seq; _, dn = np.unique(D.dia, return_inverse=True); n = len(seq)
fwd = defaultdict(list); res = defaultdict(lambda: np.zeros(3))
for t in range(1, n):
    if dn[t-1] == dn[t]:
        s1 = seq[t-1]
        if t >= 2000:
            for lo, hi, tag in [(1, 1, "1d"), (2, 7, "2-7"), (8, 30, "8-30")]:
                m = np.zeros(38, bool)
                for jd, b in fwd[s1]:
                    if lo <= dn[t] - jd <= hi: m[b] = True
                if m.any():
                    k = (D.fecha[t][:4], tag); res[k] += [m[seq[t]], P[t-2000][m].sum(), m.sum() / 38]
        fwd[s1].append((dn[t], seq[t]))
for k in sorted(res):
    o, e, u = res[k]
    print(f"{k[0]} s1->i {k[1]:5s} obs {int(o):4d} esp(ens) {e:6.1f} O/E {o/e:5.2f} z {(o-e)/np.sqrt(e):+5.2f}")
