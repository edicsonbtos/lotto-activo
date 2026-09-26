# -*- coding: utf-8 -*-
"""Variables por animal, equivariantes a permutación (sin identidad del animal).
Fila t usa solo seq[:t], dia[:t+1], hora[t] (la hora y el día del sorteo a predecir se conocen de antemano)."""
import numpy as np

K = 38
L = 72          # ventana de ganadores
LH = 11         # retardos con marca "mismo día"
NOMBRES = ([f"a{k}" for k in range(1, L + 1)] + [f"hoy{k}" for k in range(1, LH + 1)]
           + ["d0", "d1", "d2", "d3", "d4+", "dnunca"] + ["suc_s1", "pred_s1", "suc_s1_ventana"]
           + [f"hora{h}" for h in range(12)] + [f"pos{p}" for p in range(12)])
D_X = len(NOMBRES)


def construir(datos, desde, hasta=None):
    """X (hasta-desde, 38, D_X) float32. Requiere desde >= L+1."""
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); hora = np.asarray(datos.hora)
    n = len(seq) if hasta is None else hasta
    assert desde > L
    T = np.arange(desde, n)
    N = len(T)
    X = np.zeros((N, K, D_X), np.float32)
    r = np.arange(N)
    # posición en la jornada (causal: cuenta sorteos anteriores del mismo día) y s1 anterior/siguiente
    pos = np.zeros(len(seq), int)
    for t in range(1, len(seq)):
        pos[t] = pos[t - 1] + 1 if dia[t] == dia[t - 1] else 0
    # sucesor / predecesor de s1 en su ocurrencia anterior (antes de t-1)
    suc = np.full(len(seq) + 1, -1); pred = np.full(len(seq) + 1, -1)
    ult = {}
    for t in range(1, len(seq) + 1):           # en el momento t, s1 = seq[t-1]
        s1 = seq[t - 1]
        p = ult.get(s1)
        if p is not None:
            suc[t] = seq[p + 1]                # p+1 <= t-1: pasado
            pred[t] = seq[p - 1] if p >= 1 else -1
        ult[s1] = t - 1
    lastk = np.full((N, K), 10**6)
    for k in range(L, 0, -1):
        g = seq[T - k]
        X[r, g, k - 1] = 1.0
        lastk[r, g] = k
        if k <= LH:
            mismo = (dia[T - k] == dia[T])
            X[r[mismo], g[mismo], L + k - 1] = 1.0
        # nº de veces que el animal siguió a s1 dentro de la ventana
        if k >= 2:
            m = seq[T - k - 1] == seq[T - 1] if k + 1 <= L else np.zeros(N, bool)
            X[r[m], g[m], L + LH + 8] += 1.0
    o = L + LH
    vis = lastk < 10**6
    dd = np.where(vis, dia[T][:, None] - dia[np.clip(T[:, None] - np.minimum(lastk, L), 0, None)], -1)
    cat = np.where(~vis, 5, np.minimum(dd, 4))
    X[r[:, None], np.arange(K)[None, :], o + cat] = 1.0
    s, pr = suc[T], pred[T]
    X[r[s >= 0], s[s >= 0], o + 6] = 1.0
    X[r[pr >= 0], pr[pr >= 0], o + 7] = 1.0
    o2 = o + 9
    X[r, :, o2 + np.clip(hora[T], 0, 11)] = 1.0
    X[r, :, o2 + 12 + np.clip(pos[T], 0, 11)] = 1.0
    return X
