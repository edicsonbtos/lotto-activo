# -*- coding: utf-8 -*-
"""Piezas comunes de ag07: experto de recencia, variables de contexto y ajuste de la compuerta.
Todo es walk-forward: la fila t usa solo seq[:t] (y dia[:t+1], hora del sorteo t, que se conocen de antemano)."""
import numpy as np
from scipy.optimize import minimize

K = 38
GMAX = 120


def recencia(seq, n_total=None):
    """(n, 38) walk-forward. p_i ∝ (aciertos[g]+1)/(presencias[g]+38), g = sorteos desde la última salida."""
    seq = np.asarray(seq)
    n = len(seq) if n_total is None else n_total
    last = np.full(K, -10 ** 9)
    hit = np.zeros(GMAX + 1); pres = np.zeros(GMAX + 1)
    out = np.empty((n, K))
    for t in range(n):
        g = np.minimum(t - last, GMAX)
        h = (hit[g] + 1.0) / (pres[g] + K)
        out[t] = h / h.sum()
        if t < len(seq):
            np.add.at(pres, g, 1.0)
            hit[g[seq[t]]] += 1.0
            last[seq[t]] = t
    return out


def contexto(seq, dia, Lrepo):
    """X (n, 5): [1, k/11, (k/11)^2, min(r,3)/3, log38 - H]. Fila t usa seq[:t], dia[:t+1] y Lrepo[t] (walk-forward).
    Lrepo: (n, M, 38) log-probabilidades de los expertos del repo alineadas con seq."""
    seq = np.asarray(seq); dia = np.asarray(dia)
    n = len(dia)
    k = np.zeros(n); r = np.zeros(n)
    vistos = set(); kk = 0; rr = 0
    for t in range(n):
        if t == 0 or dia[t] != dia[t - 1]:
            vistos = set(); kk = 0; rr = 0
        k[t], r[t] = kk, rr
        a = seq[t]
        if a in vistos:
            rr += 1
        vistos.add(a); kk += 1
    z = Lrepo.mean(1)
    z = z - z.max(1, keepdims=True)
    p = np.exp(z); p /= p.sum(1, keepdims=True)
    H = -(p * np.log(np.clip(p, 1e-300, None))).sum(1)
    x1 = np.minimum(k, 11) / 11.0
    return np.column_stack([np.ones(n), x1, x1 ** 2, np.minimum(r, 3) / 3.0, np.log(K) - H])


def lognorm(P):
    L = np.log(np.clip(P, 1e-9, None))
    return L - np.log(np.exp(L).sum(-1, keepdims=True))


# ---------------- V1: log-lineal con pesos dependientes del contexto ----------------
def ajustar_loglineal(L, X, y, lam_a=5.0, lam_b=20.0):
    N, M, _ = L.shape
    F = X.shape[1]
    Ly = L[np.arange(N), :, y]                  # (N, M)
    prior = np.zeros((M, F)); prior[:, 0] = 1.0 / M
    lam = np.full((M, F), lam_b); lam[:, 0] = lam_a

    def f(wv):
        Wm = wv.reshape(M, F)
        A = X @ Wm.T                              # (N, M) peso por fila y experto
        z = np.einsum("nmk,nm->nk", L, A)
        zm = z.max(1, keepdims=True)
        e = np.exp(z - zm); S = e.sum(1)
        p = e / S[:, None]
        ll = (Ly * A).sum(1) - np.log(S) - zm[:, 0]
        esp = np.einsum("nk,nmk->nm", p, L)
        G = -((Ly - esp).T @ X) + lam * (Wm - prior)
        return -ll.sum() + 0.5 * np.sum(lam * (Wm - prior) ** 2), G.ravel()

    r = minimize(f, prior.ravel(), jac=True, method="L-BFGS-B", options={"maxiter": 500})
    return r.x.reshape(M, F)


def predecir_loglineal(L, X, Wm):
    z = np.einsum("nmk,nm->nk", L, X @ Wm.T)
    z -= z.max(1, keepdims=True)
    p = np.exp(z)
    return p / p.sum(1, keepdims=True)


# ---------------- V2: mezcla lineal con compuerta softmax (MoE) ----------------
def ajustar_moe(L, X, y, lam=5.0):
    N, M, _ = L.shape
    F = X.shape[1]
    Q = np.exp(L[np.arange(N), :, y])           # (N, M) prob. del ganador por experto

    def f(cv):
        C = cv.reshape(M, F)
        u = X @ C.T
        u -= u.max(1, keepdims=True)
        g = np.exp(u); g /= g.sum(1, keepdims=True)
        mix = (g * Q).sum(1)
        post = g * Q / mix[:, None]
        G = -((post - g).T @ X) + lam * C
        return -np.log(mix).sum() + 0.5 * lam * np.sum(C ** 2), G.ravel()

    r = minimize(f, np.zeros(M * F), jac=True, method="L-BFGS-B", options={"maxiter": 500})
    return r.x.reshape(M, F)


def predecir_moe(L, X, C):
    u = X @ C.T
    u -= u.max(1, keepdims=True)
    g = np.exp(u); g /= g.sum(1, keepdims=True)
    return np.einsum("nm,nmk->nk", g, np.exp(L))
