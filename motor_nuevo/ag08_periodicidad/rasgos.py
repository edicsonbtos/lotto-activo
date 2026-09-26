# -*- coding: utf-8 -*-
"""Variables indicadoras f(t, a) de ag08_periodicidad. La fila j (sorteo t = desde + j) usa SOLO
seq[:t] y el calendario (dia, hora, dow) del propio sorteo t. Admite jornadas de 11 o 12 sorteos."""
import numpy as np

K = 38
TRAMOS = [(1, 5), (6, 11), (12, 23), (24, 35), (36, 47), (48, 71), (72, 119), (120, 10**9)]


def huecos(seq, desde):
    """G[j, a] = sorteos desde la última salida de a antes de t = desde + j (10**9 si nunca)."""
    n = len(seq)
    ult = np.full(K, -10**9, dtype=np.int64)
    for t in range(desde):
        ult[seq[t]] = t
    G = np.empty((n - desde, K), dtype=np.int64)
    for t in range(desde, n):
        G[t - desde] = t - ult
        ult[seq[t]] = t
    return np.minimum(G, 10**9)


def tramo(G):
    B = np.full(G.shape, len(TRAMOS) - 1, dtype=np.int8)
    for i, (lo, hi) in enumerate(TRAMOS):
        B[(G >= lo) & (G <= hi)] = i
    return B


def mismo_hora_hace(datos, desde, k):
    """Animal que salió el día natural (dia_t − k) en la misma `hora`; −1 si no hay."""
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); hora = np.asarray(datos.hora)
    mapa = {(int(d), int(h)): int(s) for d, h, s in zip(dia, hora, seq)}  # solo días pasados se consultan
    out = np.full(len(seq) - desde, -1)
    for t in range(desde, len(seq)):
        dd = int(dia[t]) - k
        if dd < int(dia[t]):
            out[t - desde] = mapa.get((dd, int(hora[t])), -1)
    return out


def construir(datos, desde, specs):
    """X (n−desde, 38, len(specs)) con las indicadoras pedidas.
    specs: ("lag", L) | ("dia", k) | ("lagA", A, L) | ("gh", b, h) | ("gd", b, d) | ("gdh", d, h)
           | ("ah", A, h) | ("ad", A, d) | ("tab", L, delta)"""
    seq = np.asarray(datos.seq); n = len(seq); m = n - desde
    hora = np.asarray(datos.hora)[desde:]; dow = np.asarray(datos.dow)[desde:]
    X = np.zeros((m, K, len(specs)), dtype=np.float32)
    B = None; filas = np.arange(m)
    for i, s in enumerate(specs):
        tipo = s[0]
        if tipo in ("lag", "lagA", "tab"):
            L = s[1] if tipo != "lagA" else s[2]
            t = np.arange(desde, n); prev = np.where(t - L >= 0, seq[np.maximum(t - L, 0)], -1)
            ok = prev >= 0
            if tipo == "lag":
                X[filas[ok], prev[ok], i] = 1
            elif tipo == "lagA":
                A = s[1]; sel = ok & (prev == A); X[filas[sel], A, i] = 1
            else:
                a = (prev + s[2]) % K; X[filas[ok], a[ok], i] = 1
        elif tipo == "dia":
            prev = mismo_hora_hace(datos, desde, s[1]); ok = prev >= 0
            X[filas[ok], prev[ok], i] = 1
        elif tipo in ("gh", "gd", "gdh"):
            if B is None:
                B = tramo(huecos(seq, desde))
            if tipo == "gh":
                X[:, :, i] = (B == s[1]) & (hora == s[2])[:, None]
            elif tipo == "gd":
                X[:, :, i] = (B == s[1]) & (dow == s[2])[:, None]
            else:
                X[:, :, i] = ((B == 2) | (B == 3)) & ((dow == s[1]) & (hora == s[2]))[:, None]
        elif tipo == "ah":
            X[:, s[1], i] = hora == s[2]
        elif tipo == "ad":
            X[:, s[1], i] = dow == s[2]
        else:
            raise ValueError(s)
    return X


def aplicar(P_ens, X, theta):
    """P ∝ P_ens · exp(X·theta)."""
    L = np.log(np.clip(P_ens, 1e-12, None)) + X @ np.asarray(theta, np.float32)
    L -= L.max(1, keepdims=True)
    E = np.exp(L)
    return E / E.sum(1, keepdims=True)


def ajustar(P_ens, X, y, lam=1.0):
    """θ por MV condicional con offset log P_ens y ridge lam·|θ|²/2."""
    from scipy.optimize import minimize
    LP = np.log(np.clip(P_ens, 1e-12, None)); r = np.arange(len(y)); Xy = X[r, y]
    k = X.shape[2]

    def f(th):
        Z = LP + X @ th
        mx = Z.max(1, keepdims=True); E = np.exp(Z - mx); S = E.sum(1, keepdims=True)
        Q = E / S
        ll = (Z[r, y] - (mx[:, 0] + np.log(S[:, 0]))).sum()
        g = Xy.sum(0) - np.einsum("na,nak->k", Q, X)
        return -ll + lam * th @ th / 2, -g + lam * th

    res = minimize(f, np.zeros(k), jac=True, method="L-BFGS-B")
    return res.x
