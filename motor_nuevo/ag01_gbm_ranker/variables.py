# -*- coding: utf-8 -*-
"""Variables por (sorteo, animal) para ag01_gbm_ranker. Estrictamente causales:
las variables de la fila t se calculan con seq[:t] (el sorteo t se añade al estado DESPUÉS)."""
import numpy as np

K = 38
VENTANAS = (12, 24, 36, 60, 120)
NOMBRES = (["hueco1", "hueco2", "hueco_dias", "hoy", "ayer", "anteayer", "hora", "k_dia",
            "repes_dia", "desde_hoy"] + ["c%d" % w for w in VENTANAS])
NOMBRES_ENS = NOMBRES + ["ens_logp", "ens_rango"]
NF = len(NOMBRES)


def construir(seq, hora, dia, t0, t1):
    """Devuelve X (t1-t0, 38, NF) float32. Fila t usa sólo seq[:t]."""
    seq = np.asarray(seq); hora = np.asarray(hora); dia = np.asarray(dia)
    X = np.zeros((t1 - t0, K, NF), np.float32)
    last1 = np.full(K, -10 ** 6); last2 = np.full(K, -10 ** 6); lastd = np.full(K, -10 ** 6)
    por_dia = {}                       # dia -> conteos (38,)
    cum = np.zeros((t1 + 1, K), np.int32)
    hoy_n = 0; dia_act = None
    ar = np.arange(K)
    for t in range(t1):
        d = int(dia[t])
        if d != dia_act:
            dia_act = d; hoy_n = 0
            por_dia.setdefault(d, np.zeros(K, np.int32))
        if t >= t0:
            f = X[t - t0]
            hoy = por_dia[d]
            f[:, 0] = np.minimum(t - last1, 400)
            f[:, 1] = np.minimum(t - last2, 400)
            f[:, 2] = np.minimum(d - lastd, 30)
            f[:, 3] = hoy
            f[:, 4] = por_dia.get(d - 1, np.zeros(K))
            f[:, 5] = por_dia.get(d - 2, np.zeros(K))
            f[:, 6] = hora[t]
            f[:, 7] = hoy_n
            f[:, 8] = hoy_n - int((hoy > 0).sum())
            f[:, 9] = np.where(lastd == d, np.minimum(t - last1, 99), 99)
            for q, w in enumerate(VENTANAS):
                f[:, 10 + q] = cum[t] - cum[max(0, t - w)]
        s = int(seq[t])
        cum[t + 1] = cum[t]; cum[t + 1, s] += 1
        last2[s] = last1[s]; last1[s] = t; lastd[s] = d
        por_dia[d][s] += 1; hoy_n += 1
    return X


def con_ensamble(X, P_ens):
    """Añade log P_ens y el rango (1 = primero) del animal en el ensamble."""
    P = np.clip(P_ens, 1e-12, None); P = P / P.sum(1, keepdims=True)
    lp = np.log(P).astype(np.float32)
    rango = (np.argsort(np.argsort(-P, axis=1), axis=1) + 1).astype(np.float32)
    return np.concatenate([X, lp[:, :, None], rango[:, :, None]], axis=2), lp
