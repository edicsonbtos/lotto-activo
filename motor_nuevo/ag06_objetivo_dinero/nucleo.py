# -*- coding: utf-8 -*-
"""Ajustes de ag06: pérdida de dinero (rango suave del ganador, Top-5 escalonado) y log-loss de control."""
import numpy as np
from scipy.optimize import minimize

TAU, SIG, LAM = 0.25, 0.5, 1e-3


def _sig(z):
    return 0.5 * (1 + np.tanh(0.5 * z))


def ganancia(r, sig=SIG):
    return _sig((3.5 - r) / sig) + _sig((5.5 - r) / sig)


def perdida_dinero(w, L, X, y, tau=TAU, sig=SIG, lam=LAM):
    n = len(y); ar = np.arange(n)
    s = L + X @ w                                  # (n, 38)
    sw = s[ar, y]
    d = (s - sw[:, None]) / tau
    S = _sig(d); S[ar, y] = 0
    r = 1 + S.sum(1)
    a = _sig((3.5 - r) / sig); b = _sig((5.5 - r) / sig)
    G = a + b
    dG = -(a * (1 - a) + b * (1 - b)) / sig        # dG/dr
    D = S * (1 - S) / tau; D[ar, y] = 0            # dr/ds_j (j != w)
    Dw = -D.sum(1)                                  # dr/ds_w
    coef = dG[:, None] * D; coef[ar, y] = dG * Dw  # dG/ds
    grad = np.einsum("nk,nkf->f", coef, X)
    f = -G.mean() + lam * w @ w
    return f, -grad / n + 2 * lam * w


def perdida_log(w, L, X, y, lam=LAM):
    n = len(y); ar = np.arange(n)
    s = L + X @ w
    s = s - s.max(1, keepdims=True)
    e = np.exp(s); P = e / e.sum(1, keepdims=True)
    f = -np.log(P[ar, y]).mean() + lam * w @ w
    R = P.copy(); R[ar, y] -= 1
    return f, np.einsum("nk,nkf->f", R, X) / n + 2 * lam * w


def ajustar(L, X, y, tipo, w0=None, **kw):
    w0 = np.zeros(X.shape[2]) if w0 is None else np.asarray(w0, float)
    fun = perdida_dinero if tipo == "dinero" else perdida_log
    r = minimize(fun, w0, args=(L, X, y), jac=True, method="L-BFGS-B", kwargs=None) if False else \
        minimize(lambda w: fun(w, L, X, y, **kw), w0, jac=True, method="L-BFGS-B", options={"maxiter": 500})
    return r.x


def ajustar_c(s, y):
    """Escala c de softmax(c·s) por log-loss (no cambia el orden)."""
    ar = np.arange(len(y))
    def f(c):
        z = c[0] * s; z = z - z.max(1, keepdims=True)
        lse = np.log(np.exp(z).sum(1))
        e = np.exp(z - lse[:, None])
        val = -(z[ar, y] - lse).mean()
        g = -(s[ar, y] - (e * s).sum(1)).mean()
        return val, np.array([g])
    return float(minimize(f, np.array([1.0]), jac=True, method="L-BFGS-B", bounds=[(0.05, 5)]).x[0])


def softmax(z):
    z = z - z.max(1, keepdims=True); e = np.exp(z)
    return e / e.sum(1, keepdims=True)
