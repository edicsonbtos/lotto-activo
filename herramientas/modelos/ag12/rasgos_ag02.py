# -*- coding: utf-8 -*-
"""Variables de contenido para la corrección residual sobre el ensamble (ag02_residuo_boost).

construir(datos, desde) -> X (n-desde, 38, F) float32, extra (n-desde, 2) [hora, posición en la jornada].
La fila j (sorteo t = desde + j) usa SOLO datos.seq[:t] (y hora/dia de t, que son el calendario).
"""
import numpy as np

K = 38
NOMBRES = []
for s in ("s1", "s2"):
    NOMBRES += [f"{s}_vec1", f"{s}_vec23", f"{s}_col", f"{s}_fila", f"{s}_digito", f"{s}_decena"]
NOMBRES += ["s3_vec1", "s3_vec23",
            "sucesor_s1", "predecesor_s1", "sucesor_par", "mismo_dia_que_s1_ant",
            "ult_ayer_primero", "ult_ayer_resto", "ayer_misma_hora", "ayer_hora_pm1",
            "ayer_pos0_2", "ayer_pos3_5", "ayer_pos6_8", "ayer_pos9_11", "ayer_siguio_a_s1"]
F = len(NOMBRES)  # 27

_V = np.array([np.nan, np.nan] + list(range(1, 37)), float)   # 0 y 00 sin número de tablero


def _tablero(s, completo=True):
    """(38, 6 o 2) relaciones de tablero de cada candidato con el animal s."""
    out = np.zeros((K, 6 if completo else 2), np.float32)
    vs = _V[s]
    if np.isnan(vs):
        return out
    v = _V
    ok = ~np.isnan(v) & (np.arange(K) != s)
    d = np.abs(v - vs)
    out[:, 0] = ok & (d == 1)
    out[:, 1] = ok & ((d == 2) | (d == 3))
    if completo:
        with np.errstate(invalid="ignore"):
            out[:, 2] = ok & (((v - 1) % 3) == ((vs - 1) % 3))
            out[:, 3] = ok & (((v - 1) // 3) == ((vs - 1) // 3))
            out[:, 4] = ok & ((v % 10) == (vs % 10))
            out[:, 5] = ok & ((v // 10) == (vs // 10))
    return out


_TAB6 = [_tablero(s, True) for s in range(K)]
_TAB2 = [_tablero(s, False) for s in range(K)]


def construir(datos, desde):
    seq = np.asarray(datos.seq); hora = np.asarray(datos.hora); dia = np.asarray(datos.dia)
    n = len(seq)
    X = np.zeros((n - desde, K, F), np.float32)
    extra = np.zeros((n - desde, 2), np.float32)
    pos = [[] for _ in range(K)]          # posiciones de cada animal
    par = {}                               # (a,b) -> lista de índices de b
    dia_set = {}                           # día -> set de animales (solo sorteos ya pasados)
    hoy, ayer = [], []                     # [(hora, animal)] de la jornada actual y de la anterior
    dia_act = None
    for t in range(n):
        if dia[t] != dia_act:
            if dia_act is not None:
                ayer = hoy
            hoy = []; dia_act = dia[t]
        if t >= desde:
            x = X[t - desde]
            k = len(hoy)
            extra[t - desde] = (hora[t], k)
            s1 = seq[t - 1] if t >= 1 else None
            s2 = seq[t - 2] if t >= 2 else None
            s3 = seq[t - 3] if t >= 3 else None
            if s1 is not None:
                x[:, 0:6] = _TAB6[s1]
                p1 = pos[s1]
                # ocurrencia anterior de s1 (la última es t-1)
                if len(p1) >= 2:
                    p = p1[-2]
                    x[seq[p + 1], 14] = 1
                    if p >= 1:
                        x[seq[p - 1], 15] = 1
                    if dia[p] != dia[t]:
                        for a in dia_set.get(dia[p], ()):
                            x[a, 17] = 1
            if s2 is not None:
                x[:, 6:12] = _TAB6[s2]
                q = par.get((s2, s1))
                if q is not None and len(q) >= 2:
                    x[seq[q[-2] + 1], 16] = 1
            if s3 is not None:
                x[:, 12:14] = _TAB2[s3]
            if ayer:
                ult = ayer[-1][1]
                x[ult, 18 if k == 0 else 19] = 1
                h = hora[t]
                for j, (hh, a) in enumerate(ayer):
                    if hh == h:
                        x[a, 20] = 1
                    elif abs(hh - h) == 1:
                        x[a, 21] = 1
                    x[a, 22 + min(j // 3, 3)] = 1
                    if s1 is not None and a == s1 and j + 1 < len(ayer):
                        x[ayer[j + 1][1], 26] = 1
        # registrar el sorteo t (ya predicho)
        s = int(seq[t])
        pos[s].append(t)
        if t >= 1:
            par.setdefault((int(seq[t - 1]), s), []).append(t)
        dia_set.setdefault(dia[t], set()).add(s)
        hoy.append((int(hora[t]), s))
    return X, extra
