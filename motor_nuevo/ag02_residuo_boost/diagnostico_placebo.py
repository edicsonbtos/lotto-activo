# -*- coding: utf-8 -*-
"""Diagnóstico (no elige nada): ¿el efecto 'sucesor' es adyacencia o artefacto de recencia?
Compara O/E frente al ensamble de seq[p+d] (p = ocurrencia anterior de s1) para d = -3..+3,
y lo mismo tomando p = ocurrencia anterior de s2, s3 y de un animal ajeno (seq[t-6])."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI))
import arnes as A
D = A.datos().prefijo(A.CORTE); seq = D.seq; dia = D.dia
P, y = A.base(); P = P / P.sum(1, keepdims=True)
pos = [[] for _ in range(38)]
acc = {}
for t in range(len(seq)):
    if t >= A.W:
        j = t - A.W
        for lag in (1, 2, 3, 6):
            s = seq[t - lag]; ps = [q for q in pos[s] if q < t - lag]
            if not ps: continue
            p = ps[-1]
            for d in (-3, -2, -1, 1, 2, 3):
                q = p + d
                if q < 0 or q >= t - lag or q == t - lag: continue
                a = seq[q]
                if a in seq[max(0, t - 3):t]: continue    # quita los que salieron en los 3 últimos
                o, e = acc.get((lag, d), (0, 0.0))
                acc[(lag, d)] = (o + (y[j] == a), e + P[j, a])
    pos[seq[t]].append(t)
for (lag, d), (o, e) in sorted(acc.items()):
    z = (o - e) / np.sqrt(e)
    print(f"ancla s{lag}  desplaz {d:+d}: O={o:4d} E={e:7.1f} O/E={o/e:.3f} z={z:+.2f}")
