# -*- coding: utf-8 -*-
"""Variables de contexto (ag06). construir(datos, desde) -> X (n-desde, 38, F) float32.
La fila j (sorteo t = desde+j) usa SOLO seq[:t] (y hora/dia de t, que son calendario)."""
import numpy as np

K = 38
NOMBRES = ["s1_vec1", "s1_digito", "s1_col", "sucesor_s1", "predecesor_s1",
           "ult_ayer", "ayer_misma_hora", "hueco_12_23", "hueco_24_35"]
F = len(NOMBRES)
_V = np.array([np.nan, np.nan] + list(range(1, 37)), float)


def _tab(s):
    out = np.zeros((K, 3), np.float32)
    vs = _V[s]
    if np.isnan(vs):
        return out
    ok = ~np.isnan(_V) & (np.arange(K) != s)
    with np.errstate(invalid="ignore"):
        out[:, 0] = ok & (np.abs(_V - vs) == 1)
        out[:, 1] = ok & ((_V % 10) == (vs % 10))
        out[:, 2] = ok & (((_V - 1) % 3) == ((vs - 1) % 3))
    return out


_TAB = [_tab(s) for s in range(K)]


def construir(datos, desde):
    seq = np.asarray(datos.seq); hora = np.asarray(datos.hora); dia = np.asarray(datos.dia)
    n = len(seq)
    X = np.zeros((n - desde, K, F), np.float32)
    pos = [[] for _ in range(K)]
    ult = np.full(K, -10**9)
    hoy, ayer, dia_act = [], [], None
    for t in range(n):
        if dia[t] != dia_act:
            if dia_act is not None:
                ayer = hoy
            hoy, dia_act = [], dia[t]
        if t >= desde:
            x = X[t - desde]
            if t >= 1:
                s1 = int(seq[t - 1])
                x[:, 0:3] = _TAB[s1]
                p1 = pos[s1]
                if len(p1) >= 2:
                    p = p1[-2]
                    x[seq[p + 1], 3] = 1
                    if p >= 1:
                        x[seq[p - 1], 4] = 1
            if ayer:
                x[ayer[-1][1], 5] = 1
                for hh, a in ayer:
                    if hh == hora[t]:
                        x[a, 6] = 1
            g = t - ult
            x[:, 7] = (g >= 12) & (g <= 23)
            x[:, 8] = (g >= 24) & (g <= 35)
        s = int(seq[t])
        pos[s].append(t); ult[s] = t
        hoy.append((int(hora[t]), s))
    return X
