# -*- coding: utf-8 -*-
"""Hilo 7 (E1): B1 = B0 de RD Int + memoria cruzada de Lotto Activo.

B0: un modelo de herramientas/modelos/ (secuencia_v3 o intradia_v2) corrido SOLO con la
    secuencia de RD Int. Da P0 (n-desde, 38), fila j = sorteo desde+j con RD hasta t-1.
B1: logit condicional apilado sobre B0
        P1[t, i] ~ P0[t, i] * exp(b . x_i(t))
    x_i(t) = [ la_h[t]==i , la_h1[t]==i , la_hoy[t,i]>0 y i no es la_h ni la_h1 ]
    (Lotto Activo de h:00 y antes del MISMO dia: sale 30 min antes que RD Int h:30).
    b se ajusta por MLE + L2 ligera cada R filas usando SOLO las filas anteriores
    (y de esas filas ya ocurrio); con menos de `minimo` filas, b = 0.
"""
import os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import lotto_eval as LE

K = LE.K
NOMBRES = ["LA h:00", "LA (h-1):00", "LA antes hoy"]


def features(la_h, la_h1, la_hoy):
    """(n, 38, 3) float32. Si la_h o la_h1 == -1 su indicador es 0."""
    n = len(la_h); ar = np.arange(n)
    X = np.zeros((n, K, 3), np.float32)
    ok = la_h >= 0; X[ar[ok], la_h[ok], 0] = 1
    ok = la_h1 >= 0; X[ar[ok], la_h1[ok], 1] = 1
    X[:, :, 2] = (la_hoy > 0) & (X[:, :, 0] == 0) & (X[:, :, 1] == 0)
    return X


def ajustar(logP0, X, y, lam=1.0, iters=30):
    """MLE de b con offset logP0 y prior N(0, 1/lam). Newton amortiguado."""
    N, _, d = X.shape; rows = np.arange(N)
    Xy = X[rows, y].astype(np.float64).sum(0)
    b = np.zeros(d)

    def valor(b):
        z = logP0 + (X @ b.astype(np.float32)).astype(np.float64)
        zm = z.max(1, keepdims=True); e = np.exp(z - zm); S = e.sum(1)
        f = -(z[rows, y] - np.log(S) - zm[:, 0]).sum() + 0.5 * lam * b @ b
        return f, e / S[:, None]

    f, p = valor(b)
    for _ in range(iters):
        M = np.einsum("nk,nkd->nd", p, X)
        g = M.sum(0) - Xy + lam * b
        H = np.einsum("nk,nkd,nke->de", p, X, X) - M.T @ M + lam * np.eye(d)
        paso = np.linalg.solve(H, g); t = 1.0
        while True:
            nb = b - t * paso; nf, npp = valor(nb)
            if nf <= f + 1e-9 or t < 1e-3:
                break
            t *= 0.5
        b, f, p = nb, nf, npp
        if np.abs(t * paso).max() < 1e-7:
            break
    return b


def cruzado(P0, X, y, R=250, minimo=500, lam=1.0):
    """P1 walk-forward. P0, X, y alineados (fila j = mismo sorteo).
    Devuelve (P1, historia) con historia = [(fila_inicio_bloque, b)]."""
    P0 = LE.normalizar(P0); L0 = np.log(P0)
    n = len(P0); P1 = np.empty_like(P0); b = np.zeros(X.shape[2]); hist = []
    for T in range(0, n, R):
        if T >= minimo:
            b = ajustar(L0[:T], X[:T], y[:T], lam)
        hist.append((T, b.copy()))
        s = slice(T, min(T + R, n))
        z = L0[s] + (X[s] @ b.astype(np.float32)).astype(np.float64)
        z -= z.max(1, keepdims=True); p = np.exp(z)
        P1[s] = p / p.sum(1, keepdims=True)
    return P1, hist


def predecir(modelo_b0, rd, la_h, la_h1, la_hoy, desde, **kw):
    """Tuberia completa B0 -> B1 sobre filas desde..n-1. Devuelve (P0, P1, hist)."""
    P0 = LE.normalizar(modelo_b0.predecir(rd, desde))
    X = features(la_h, la_h1, la_hoy)[desde:]
    P1, hist = cruzado(P0, X, np.asarray(rd.seq)[desde:], **kw)
    return P0, P1, hist


def prueba_fuga(modelo_b0, rd, la_h, la_h1, la_hoy, desde, cortes=2, semilla=0, base=None):
    """Baraja RD desde c y Lotto Activo desde c+1 (la fila c usa LA de su propio h:00, legitimo);
    exige que las filas desde..c de P0 y P1 no cambien."""
    rng = np.random.default_rng(semilla); n = len(rd)
    if base is None:
        base = predecir(modelo_b0, rd, la_h, la_h1, la_hoy, desde)
    res = []
    for c in sorted(rng.integers(desde + 600, n - 50, size=cortes)):
        s2 = np.asarray(rd.seq).copy(); s2[c:] = rng.integers(0, K, size=n - c)
        rd2 = LE.Datos(s2, rd.hora, rd.dow, rd.dia, rd.fecha)
        h2 = la_h.copy(); h2[c + 1:] = rng.integers(0, K, size=n - c - 1)
        g2 = la_h1.copy(); g2[c + 1:] = rng.integers(0, K, size=n - c - 1)
        y2 = la_hoy.copy(); y2[c + 1:] = rng.integers(0, 2, size=y2[c + 1:].shape)
        P0b, P1b, _ = predecir(modelo_b0, rd2, h2, g2, y2, desde)
        f = c - desde + 1
        d0 = float(np.max(np.abs(base[0][:f] - P0b[:f]))); d1 = float(np.max(np.abs(base[1][:f] - P1b[:f])))
        # control: el futuro SI debe cambiar (si no, la prueba no prueba nada)
        dfut = float(np.max(np.abs(base[1][f:] - P1b[f:])))
        res.append((int(c), d0, d1, dfut))
    ok = all(d0 <= 1e-9 and d1 <= 1e-9 for _, d0, d1, _ in res)
    return ok, res
