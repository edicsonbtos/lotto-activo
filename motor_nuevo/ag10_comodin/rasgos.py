# -*- coding: utf-8 -*-
"""ag10_comodin: variables de composición del día / anti-déjà-vu (ver PREREGISTRO.md).

construir(datos, desde) -> X (n-desde, 38, 9) float. La fila t usa solo seq[:t] (y el calendario:
dia de t, que se conoce antes del sorteo). Funciona con jornadas de 11 o 12 sorteos.
"""
import numpy as np

K = 38
NOMBRES = ["ayer_cooc", "sem_cooc", "mes_cooc", "trans1_30", "trans2_30", "orden_30",
           "ayer_x_S", "nsem_x_S", "nmes_x_S"]


def construir(datos, desde):
    seq = np.asarray(datos.seq, int)
    dia = np.asarray(datos.dia, int)
    n = len(seq)
    X = np.zeros((n - desde, K, len(NOMBRES)))
    # jornadas en orden; primera fila de cada jornada
    dias_u, ini = np.unique(dia, return_index=True)
    fin = np.append(ini[1:], n)
    # matrices por jornada (solo se usan jornadas estrictamente anteriores a la de t,
    # que están completas antes de t)
    ND = len(dias_u)
    M = np.zeros((ND, K))
    POS = np.full((ND, K), -1)
    for k in range(ND):
        for p, u in enumerate(range(ini[k], fin[k])):
            M[k, seq[u]] = 1
            POS[k, seq[u]] = p
    kd_de = np.searchsorted(dias_u, dia)             # índice de jornada de cada fila
    cache_dia = {}
    for t in range(desde, n):
        kd = kd_de[t]; d = dia[t]
        if kd not in cache_dia:
            cache_dia.clear()
            ksem = (np.searchsorted(dias_u, d - 7), np.searchsorted(dias_u, d - 1))      # [d-7, d-2]
            kmes = (np.searchsorted(dias_u, d - 30), np.searchsorted(dias_u, d - 7))     # [d-30, d-8]
            k30 = (np.searchsorted(dias_u, d - 30), kd)                                  # [d-30, d-1]
            MW, MM = M[ksem[0]:ksem[1]], M[kmes[0]:kmes[1]]
            P30 = POS[k30[0]:k30[1]]
            Y1 = M[kd - 1] if kd >= 1 else np.zeros(K)
            u30 = np.searchsorted(dia, d - 30)       # primera fila con dia >= d-30
            cache_dia[kd] = (MW, MM, P30, Y1, u30)
        MW, MM, P30, Y1, u30 = cache_dia[kd]
        S = seq[ini[kd]:t]
        nS = len(S)
        x = X[t - desde]
        if nS:
            x[:, 0] = Y1 * Y1[S].sum()
            cw = MW[:, S].sum(1); x[:, 1] = MW.T @ cw
            cm = MM[:, S].sum(1); x[:, 2] = MM.T @ cm
            # quitar el par (i, i) cuando i ya salió hoy
            x[S, 1] -= MW[:, S].sum(0)
            x[S, 2] -= MM[:, S].sum(0)
            pres = P30 >= 0
            for b in S:
                pb = P30[:, b]
                ok = (pb >= 0)[:, None] & pres & (P30 > pb[:, None])
                x[:, 5] += ok.sum(0)
            x[:, 6] = Y1 * nS
            x[:, 7] = nS * MW.sum(0)
            x[:, 8] = nS * MM.sum(0)
        lo = max(u30, 2)
        if t >= 1 and t > lo:
            s1 = seq[t - 1]
            u = np.arange(lo, t)
            x[:, 3] = np.bincount(seq[u][seq[u - 1] == s1], minlength=K)
            if t >= 2:
                s2 = seq[t - 2]
                x[:, 4] = np.bincount(seq[u][seq[u - 2] == s2], minlength=K)
    return X
