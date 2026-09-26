# -*- coding: utf-8 -*-
"""ag09_multi_escala: variables multi-escala de reciclaje (dispersas) y ajuste del logit condicional penalizado.

construir(datos, desde) -> X (csr, (n-desde)*38 x P): fila j*38+a = sorteo t=desde+j, animal a.
La fila t usa SOLO datos.seq[:t] (hora/dia de t son calendario).
"""
import numpy as np
import scipy.sparse as sp
from scipy.interpolate import BSpline
from scipy.optimize import minimize

K = 38
NB, TOPE = 12, 300
H = 12
# columnas
C_GAP = 0
C_S1 = C_GAP + NB
C_S2 = C_S1 + H * H
C_GD = C_S2 + H * H
C_C3 = C_GD + 9
C_HOY = C_C3 + 4
C_AN = C_HOY + 1
P = C_AN + K          # 352
GRUPOS = {"gap": (C_GAP, C_S1), "sup1": (C_S1, C_S2), "sup2": (C_S2, C_GD), "gd": (C_GD, C_C3),
          "c3": (C_C3, C_HOY), "hoy": (C_HOY, C_AN), "animal": (C_AN, P)}


def _tabla_spline():
    grado = 3
    lo, hi = 0.0, np.log(TOPE)
    interior = np.linspace(lo, hi, NB - grado + 1)
    t = np.r_[[lo] * grado, interior, [hi] * grado]
    x = np.log(np.arange(1, TOPE + 1, dtype=float))
    x[-1] = hi - 1e-9
    B = BSpline.design_matrix(x, t, grado).toarray()
    assert B.shape == (TOPE, NB)
    return B  # fila g-1 = hueco g (1..TOPE)


_B = _tabla_spline()


def construir(datos, desde):
    seq = np.asarray(datos.seq); hora = np.asarray(datos.hora); dia = np.asarray(datos.dia)
    n = len(seq)
    last = np.full(K, -1, np.int64)
    hist_dias = [[] for _ in range(K)]      # días (con repetición) de cada salida
    filas, cols, vals = [], [], []
    a_idx = np.arange(K)
    for t in range(desde):
        s = int(seq[t]); last[s] = t; hist_dias[s].append(dia[t])
    for t in range(desde, n):
        base = (t - desde) * K
        visto = last >= 0
        gs = np.where(visto, t - last, TOPE)
        gs = np.clip(gs, 1, TOPE)
        Bg = _B[gs - 1]                                  # (38, NB)
        r = np.repeat(base + a_idx, NB); c = np.tile(C_GAP + np.arange(NB), K)
        filas.append(r); cols.append(c); vals.append(Bg.ravel())
        dl = np.where(visto, dia[np.maximum(last, 0)], -10 ** 6)
        hl = np.where(visto, hora[np.maximum(last, 0)], 0)
        gd = dia[t] - dl
        hn = int(hora[t])
        # superficies
        for g, c0 in ((1, C_S1), (2, C_S2)):
            m = visto & (gd == g)
            if m.any():
                filas.append(base + a_idx[m]); cols.append(c0 + hl[m] * H + hn); vals.append(np.ones(m.sum()))
        gdc = np.where(visto, np.minimum(gd, 8), 8)
        filas.append(base + a_idx); cols.append(C_GD + gdc); vals.append(np.ones(K))
        # c3: veces en los 3 días anteriores
        c3 = np.zeros(K, np.int64)
        for a in range(K):
            hd = hist_dias[a]
            k = 0
            for d in reversed(hd):
                if d >= dia[t]:
                    continue
                if d < dia[t] - 3:
                    break
                k += 1
            c3[a] = min(k, 3)
        filas.append(base + a_idx); cols.append(C_C3 + c3); vals.append(np.ones(K))
        m = visto & (gd == 0)
        if m.any():
            filas.append(base + a_idx[m]); cols.append(np.full(m.sum(), C_HOY)); vals.append(np.ones(m.sum()))
        filas.append(base + a_idx); cols.append(C_AN + a_idx); vals.append(np.ones(K))
        s = int(seq[t]); last[s] = t; hist_dias[s].append(dia[t])
    X = sp.csr_matrix((np.concatenate(vals), (np.concatenate(filas), np.concatenate(cols))),
                      shape=((n - desde) * K, P))
    return X


def _dif(m, orden):
    D = np.eye(m)
    for _ in range(orden):
        D = np.diff(D, axis=0)
    return D


def penalizacion():
    S = np.zeros((P, P))
    D2 = _dif(NB, 2); S[C_GAP:C_S1, C_GAP:C_S1] = D2.T @ D2
    D1 = _dif(H, 1); I = np.eye(H)
    S2d = np.kron(D1.T @ D1, I) + np.kron(I, D1.T @ D1) + 0.01 * np.eye(H * H)
    S[C_S1:C_S2, C_S1:C_S2] = S2d
    S[C_S2:C_GD, C_S2:C_GD] = S2d
    for c0, c1 in ((C_GD, C_C3), (C_C3, C_HOY), (C_HOY, C_AN), (C_AN, P)):
        S[c0:c1, c0:c1] = np.eye(c1 - c0)
    return S


S_PEN = penalizacion()


def filas_X(X, idx):
    """Submatriz de X para los sorteos idx (índices de fila de sorteo)."""
    r = (np.asarray(idx)[:, None] * K + np.arange(K)).ravel()
    return X[r]


def ajustar(X, off, y, lam, w0=None):
    """X csr (n*38,P), off (n,38) log P_base, y (n,). Minimiza -loglik + 0.5 w'(lam S + 1e-3 I)w."""
    n = len(y)
    A = lam * S_PEN + 1e-3 * np.eye(P)
    XT = X.T.tocsr()
    ar = np.arange(n)

    def f(w):
        z = off + (X @ w).reshape(n, K)
        z = z - z.max(1, keepdims=True)
        lse = np.log(np.exp(z).sum(1))
        ll = (z[ar, y] - lse).sum()
        p = np.exp(z - lse[:, None]); p[ar, y] -= 1
        g = XT @ p.ravel() + A @ w
        return -ll + 0.5 * w @ A @ w, g

    r = minimize(f, np.zeros(P) if w0 is None else w0, jac=True, method="L-BFGS-B",
                 options={"maxiter": 2000, "gtol": 1e-6})
    return r.x


def predecir_log(X, off, w):
    n = off.shape[0]
    z = off + (X @ w).reshape(n, K)
    z = z - z.max(1, keepdims=True)
    Q = np.exp(z)
    return Q / Q.sum(1, keepdims=True)


def loglik(X, off, y, w):
    Q = predecir_log(X, off, w)
    return float(np.log(np.clip(Q[np.arange(len(y)), y], 1e-300, None)).sum())


def bloques_dia(dia, k):
    """Divide las filas en k bloques CONTIGUOS de jornadas completas. Devuelve etiqueta por fila."""
    u = np.unique(dia)
    cortes = np.array_split(u, k)
    lab = np.zeros(len(dia), int)
    for b, dd in enumerate(cortes):
        lab[np.isin(dia, dd)] = b
    return lab


LAMS = (0.3, 3.0, 30.0, 300.0)


def elegir_lam(X, off, y, dia, k=4, lams=LAMS):
    lab = bloques_dia(dia, k)
    punt = []
    for lam in lams:
        s = 0.0
        for b in range(k):
            tr, te = np.where(lab != b)[0], np.where(lab == b)[0]
            w = ajustar(filas_X(X, tr), off[tr], y[tr], lam)
            s += loglik(filas_X(X, te), off[te], y[te], w)
        punt.append(s)
    return lams[int(np.argmax(punt))], punt
