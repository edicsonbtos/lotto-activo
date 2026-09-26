# -*- coding: utf-8 -*-
"""Núcleo de ag04: ensamble log-lineal con reajuste periódico (réplica de ensamble.py) y filtro de
Kalman (Laplace) sobre los pesos. L: (n, M, K) log-probabilidades de los submodelos, fila i = sorteo
a0+i, calculadas walk-forward. La predicción de la fila i usa solo y[:i]."""
import importlib.util, os
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
_spec = importlib.util.spec_from_file_location("ensamble_base", os.path.join(RAIZ, "herramientas", "modelos", "ensamble.py"))
_E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_E)


def _softmax_mix(Lb, w):
    z = np.einsum("nmk,m->nk", Lb, w)
    z -= z.max(1, keepdims=True)
    p = np.exp(z)
    return p / p.sum(1, keepdims=True)


def ensamble_refit(L, y, desde, R=250, tau=3000.0, lam=5.0):
    """Igual que ensamble.Modelo.predecir: filas [desde, n) de L; bloque [T, T+R) con w ajustado en L[:T]."""
    n, M, _ = L.shape
    w = np.full(M, 1.0 / M)
    out = np.empty((n - desde, L.shape[2])); hist = []
    for T in range(desde, n, R):
        if T >= 200:
            pt = np.exp(-(T - 1 - np.arange(T)) / tau) if tau else None
            w = _E.ajustar_pesos(L[:T], y[:T], w, lam, pt)
        hist.append((T, w.copy()))
        b = min(T + R, n)
        out[T - desde:b - desde] = _softmax_mix(L[T:b], w)
    return out, hist


def kalman(L, y, q=1e-5, s0=0.1, w0=None):
    """Filtro de Kalman extendido (Laplace) con paseo aleatorio sobre w. Devuelve P (n, K) para todas
    las filas de L (la fila i usa w tras actualizar con y[:i]) y la trayectoria de w."""
    n, M, K = L.shape
    w = np.full(M, 1.0 / M) if w0 is None else np.asarray(w0, float).copy()
    S = np.eye(M) * s0; Q = np.eye(M) * q
    out = np.empty((n, K)); Wt = np.empty((n, M))
    for i in range(n):
        S = S + Q
        Li = L[i]                       # (M, K)
        z = w @ Li; z -= z.max()
        p = np.exp(z); p /= p.sum()
        out[i] = p; Wt[i] = w
        if y is None or i >= len(y):
            continue
        m = Li @ p                      # E_p[L_m]
        g = Li[:, y[i]] - m
        C = (Li * p) @ Li.T - np.outer(m, m)
        S = np.linalg.inv(np.linalg.inv(S) + C)
        S = 0.5 * (S + S.T)
        w = w + S @ g
    return out, Wt
