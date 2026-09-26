# -*- coding: utf-8 -*-
"""Variables de los modelos generativos "baraja" (ag05). La fila t usa SOLO seq[:t] y el calendario
(fecha natural) del sorteo t. Devuelven X (n - desde, 38, p) float32.

Familias (ver PREREGISTRO.md):
  ("G1",)          : [salió hoy]
  ("G2", D, phi)   : [salió hoy, salió en el mazo actual antes de hoy]; mazo = bloque de D días
                     naturales anclado a date.toordinal() (fase absoluta, portable a otro historial)
  ("G3", phi)      : [salió hoy, salió en el mazo de 38 sorteos actual]; mazo por índice global
                     (NO portable: depende del inicio del archivo)
  ("G4", N)        : [salió hoy, cuenta últimos N == 1, cuenta últimos N >= 2]
  ("G5",)          : one-hot días desde la última aparición (0=hoy, 1, 2, 3, 4+)
"""
from datetime import date
import numpy as np

K = 38


def ordinales(datos):
    cache = {}
    out = np.empty(len(datos.seq), np.int64)
    for i, f in enumerate(datos.fecha):
        o = cache.get(f)
        if o is None:
            o = cache[f] = date.fromisoformat(f).toordinal()
        out[i] = o
    return out


def estado(datos):
    """Precalcula por fila t (estado ANTES del sorteo t): cuenta hoy, último día visto (ordinal)."""
    seq = np.asarray(datos.seq); n = len(seq); od = ordinales(datos)
    HOY = np.zeros((n, K), np.int8); LASTD = np.empty((n, K), np.int64)
    cnt = np.zeros(K, np.int8); lastd = np.full(K, -10**6); cur = None
    for t in range(n):
        if od[t] != cur:
            cnt[:] = 0; cur = od[t]
        HOY[t] = cnt; LASTD[t] = lastd
        v = seq[t]; cnt[v] += 1; lastd[v] = od[t]
    return seq, od, HOY, LASTD


def construir(datos, desde, cfg, st=None):
    seq, od, HOY, LASTD = st if st is not None else estado(datos)
    n = len(seq); r = slice(desde, n)
    hoy = (HOY[r] > 0).astype(np.float32)
    fam = cfg[0]
    if fam == "G1":
        return hoy[:, :, None]
    if fam == "G2":
        D, phi = cfg[1], cfg[2]
        o = od[r]
        inicio = o - ((o - phi) % D)                 # primer día del mazo actual
        prev = ((LASTD[r] >= inicio[:, None]) & (LASTD[r] < o[:, None])).astype(np.float32)
        return np.stack([hoy, prev], -1)
    if fam == "G3":
        phi = cfg[1]
        ini_all = np.arange(n) - ((np.arange(n) - phi) % 38)
        f = np.zeros((n - desde, K), np.float32)
        last = np.full(K, -10**9)
        for t in range(n):
            if t >= desde:
                f[t - desde] = last >= ini_all[t]
            last[seq[t]] = t
        return np.stack([hoy, f], -1)
    if fam == "G4":
        N = cfg[1]
        C = np.zeros((n + 1, K), np.int32)
        np.add.at(C, (np.arange(1, n + 1), seq), 1)
        C = np.cumsum(C, 0)                            # C[t] = cuentas en seq[:t]
        idx = np.arange(desde, n)
        c = C[idx] - C[np.maximum(idx - N, 0)]
        return np.stack([hoy, (c == 1).astype(np.float32), (c >= 2).astype(np.float32)], -1)
    if fam == "G5":
        d = od[r][:, None] - LASTD[r]
        d = np.minimum(d, 4)
        return np.stack([(d == k).astype(np.float32) for k in range(4)], -1)   # 4+ = referencia
    raise ValueError(cfg)


def configs():
    c = [("G1",)]
    c += [("G2", D, p) for D in (2, 3, 4) for p in range(D)]
    c += [("G3", p) for p in range(38)]
    c += [("G4", N) for N in (12, 24, 36, 48, 72)]
    c += [("G5",)]
    return c


def nombre(cfg):
    return "_".join(str(x) for x in cfg)


# ---------------- logit condicional con offset ----------------
def ajustar(X, y, off=None, l2=1e-3):
    from scipy.optimize import minimize
    n, k, p = X.shape
    X64 = X.astype(np.float64)
    O = np.zeros((n, k)) if off is None else off
    rows = np.arange(n)

    def f(th):
        s = O + X64 @ th
        m = s.max(1, keepdims=True); e = np.exp(s - m); Z = e.sum(1, keepdims=True); P = e / Z
        ll = s[rows, y] - m[:, 0] - np.log(Z[:, 0])
        g = -(X64[rows, y] - np.einsum("nk,nkp->np", P, X64)).sum(0)
        return -ll.sum() + l2 * th @ th, g + 2 * l2 * th

    res = minimize(f, np.zeros(p), jac=True, method="L-BFGS-B")
    return res.x, -res.fun


def logp(X, th, off=None):
    s = X.astype(np.float64) @ th
    if off is not None:
        s = s + off
    s = s - s.max(1, keepdims=True)
    return s - np.log(np.exp(s).sum(1, keepdims=True))
