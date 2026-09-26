# -*- coding: utf-8 -*-
"""Rasgos ag12: 27 de ag02 + 6 de transiciones recientes (s1->i y i->s1 en ventanas de días). Fila t usa solo seq[:t]."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "ag02_residuo_boost"))
import rasgos as R2  # noqa: E402

K = 38
NUEVOS = ["T1_s1i_1d", "T2_s1i_2a7", "T3_s1i_8a30", "R1_is1_1d", "R2_is1_2a7", "R3_is1_8a30"]
NOMBRES = R2.NOMBRES + NUEVOS
F = len(NOMBRES)
VENT = [(1, 1), (2, 7), (8, 30)]


def transiciones(datos, desde):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia)
    _, dn = np.unique(dia, return_inverse=True)
    n = len(seq)
    X = np.zeros((n - desde, K, 6), np.float32)
    fwd = {}  # a -> list of (jornada, b) con b siguiendo a a dentro del día
    bwd = {}  # b -> list of (jornada, a)
    for t in range(n):
        if t >= desde and t >= 1 and dn[t - 1] == dn[t]:
            s1 = int(seq[t - 1]); d = dn[t]; x = X[t - desde]
            for (jd, b) in fwd.get(s1, ()):
                age = d - jd
                for v, (lo, hi) in enumerate(VENT):
                    if lo <= age <= hi: x[b, v] += 1
            for (jd, a) in bwd.get(s1, ()):
                age = d - jd
                for v, (lo, hi) in enumerate(VENT):
                    if lo <= age <= hi: x[a, 3 + v] += 1
        if t >= 1 and dn[t - 1] == dn[t]:
            a, b = int(seq[t - 1]), int(seq[t])
            fwd.setdefault(a, []).append((dn[t], b))
            bwd.setdefault(b, []).append((dn[t], a))
    return np.log1p(X)


def construir(datos, desde):
    X2, extra = R2.construir(datos, desde)
    return np.concatenate([X2, transiciones(datos, desde)], axis=2), extra
