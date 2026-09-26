# -*- coding: utf-8 -*-
"""MLP compartido entre animales (equivariante): logit_i = off_i + w2 · relu(W1 x_i + b1)."""
import numpy as np

H = 32


def iniciar(d, semilla=0):
    rng = np.random.default_rng(semilla)
    return {"W1": (rng.standard_normal((d, H)) * np.sqrt(2.0 / d)).astype(np.float32),
            "b1": np.zeros(H, np.float32),
            "w2": (rng.standard_normal(H) * 1e-3).astype(np.float32)}


def logits(p, X, off=None):
    Z = np.maximum(X @ p["W1"] + p["b1"], 0) @ p["w2"]
    return Z if off is None else Z + off


def probs(p, X, off=None, lote=1024):
    out = np.empty(X.shape[:2])
    for i in range(0, len(X), lote):
        z = logits(p, X[i:i + lote], None if off is None else off[i:i + lote]).astype(float)
        z -= z.max(1, keepdims=True); e = np.exp(z)
        out[i:i + lote] = e / e.sum(1, keepdims=True)
    return out


def nll(p, X, y, off=None):
    P = probs(p, X, off)
    return float(-np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-12, None))))


def _grad(p, X, y, off):
    pre = X @ p["W1"] + p["b1"]
    Hh = np.maximum(pre, 0)
    z = Hh @ p["w2"]
    if off is not None:
        z = z + off
    z = z - z.max(1, keepdims=True); e = np.exp(z); P = e / e.sum(1, keepdims=True)
    B = len(y)
    dz = P.copy(); dz[np.arange(B), y] -= 1; dz /= B            # (B, 38)
    g = {"w2": np.einsum("bkh,bk->h", Hh, dz)}
    dpre = (dz[:, :, None] * p["w2"][None, None, :]) * (pre > 0)
    g["W1"] = np.einsum("bkd,bkh->dh", X, dpre)
    g["b1"] = dpre.sum((0, 1))
    return g


def entrenar(X, y, off=None, idx_val=None, idx_tr=None, epocas=40, fijo=None, lr=1e-3, l2=1e-4,
             lote=256, paciencia=4, semilla=0):
    """Adam. Si fijo (int) se entrena ese nº de épocas sin validación. Devuelve (params, épocas_usadas)."""
    rng = np.random.default_rng(semilla)
    p = iniciar(X.shape[2], semilla)
    m = {k: np.zeros_like(v) for k, v in p.items()}; v2 = {k: np.zeros_like(v) for k, v in p.items()}
    b1, b2, eps, paso = 0.9, 0.999, 1e-8, 0
    tr = np.arange(len(y)) if idx_tr is None else idx_tr
    mejor, mejor_p, mejor_e, sin = np.inf, None, 0, 0
    n_ep = fijo if fijo is not None else epocas
    for ep in range(1, n_ep + 1):
        perm = rng.permutation(tr)
        for i in range(0, len(perm), lote):
            b = perm[i:i + lote]
            g = _grad(p, X[b], y[b], None if off is None else off[b])
            paso += 1
            for k in p:
                gk = g[k] + (l2 * p[k] if k != "b1" else 0)
                m[k] = b1 * m[k] + (1 - b1) * gk
                v2[k] = b2 * v2[k] + (1 - b2) * gk * gk
                mh = m[k] / (1 - b1 ** paso); vh = v2[k] / (1 - b2 ** paso)
                p[k] = (p[k] - lr * mh / (np.sqrt(vh) + eps)).astype(np.float32)
        if fijo is None:
            val = nll(p, X[idx_val], y[idx_val], None if off is None else off[idx_val])
            if val < mejor - 1e-6:
                mejor, mejor_p, mejor_e, sin = val, {k: q.copy() for k, q in p.items()}, ep, 0
            else:
                sin += 1
                if sin >= paciencia:
                    break
    if fijo is not None:
        return p, fijo
    return mejor_p, mejor_e
