# -*- coding: utf-8 -*-
"""Combinador (mismo procedimiento que herramientas/modelos/ensamble.py) y metricas."""
import importlib.util, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, HERR)
import lotto_eval as LE
_s = importlib.util.spec_from_file_location("ensamble", os.path.join(HERR, "modelos", "ensamble.py"))
ENS = importlib.util.module_from_spec(_s); _s.loader.exec_module(ENS)
K = 38; ARRANQUE = 1000
F5 = np.array([2, 2, 2, 1, 1] + [0] * (K - 5), float)
F15 = np.array([3, 3, 3, 2, 2] + [1] * 10 + [0] * (K - 15), float)
F15P = np.array([1] * 15 + [0] * (K - 15), float)
GRUPOS = {"base": ["I", "S", "H"], "V1": ["I_v1", "S_v1", "H_v1"], "V2": ["I_v2", "S_v2", "H_v2"],
          "V3": ["I_v3", "S_v3", "H_v3"], "V4": ["I", "S", "H", "I_v1", "S_v1", "H_v1"]}
COMB = {"base": dict(R=250, tau=3000.0, ventana=None), "V1": dict(R=250, tau=1000.0, ventana=None),
        "V2": dict(R=250, tau=None, ventana=2200), "V3": dict(R=84, tau=3000.0, ventana=None),
        "V4": dict(R=250, tau=3000.0, ventana=None)}

def cargar_L(fase, claves):
    L = np.stack([np.log(np.clip(np.load(os.path.join(AQUI, "cache", f"{fase}_{c}.npy")).astype(np.float64), 1e-9, None))
                  for c in claves], axis=1)
    L -= np.log(np.exp(L).sum(2, keepdims=True))
    return L                                   # (n - ARRANQUE, M, K)

def combinar(L, y, desde, R=250, tau=3000.0, ventana=None, lam=5.0, devolver_w=False):
    """Igual que ensamble.Modelo.predecir: el bloque [T, T+R) usa pesos ajustados con filas < T. L,y desde ARRANQUE."""
    a = ARRANQUE; n = a + len(y); M = L.shape[1]
    w = np.full(M, 1.0 / M); out = np.empty((n - desde, K)); hist = []
    for T in range(desde, n, R):
        j = T - a
        if j >= 200:
            if ventana is not None:
                lo = max(0, j - ventana); pw = np.ones(j - lo)
                w = ENS.ajustar_pesos(L[lo:j], y[lo:j], w, lam, pw)
            else:
                pw = np.exp(-(j - 1 - np.arange(j)) / tau) if tau else None
                w = ENS.ajustar_pesos(L[:j], y[:j], w, lam, pw)
        hist.append((T, w.copy()))
        b = min(T + R, n)
        z = np.einsum("nmk,m->nk", L[T - a:b - a], w); z -= z.max(1, keepdims=True)
        p = np.exp(z); out[T - desde:b - desde] = p / p.sum(1, keepdims=True)
    return (out, hist) if devolver_w else out

def por_sorteo(P, y):
    """Vectores por sorteo: bits*1000, top5, top15, retorno/ficha T5 escalonado, T15 ponderado, T15 plano."""
    P = LE.normalizar(P); n = len(y)
    orden = LE.rankings(P); pos = np.argmax(orden == y[:, None], axis=1)
    mb = np.log2(P[np.arange(n), y] * K) * 1000
    return dict(mb=mb, t5=(pos < 5).astype(float), t15=(pos < 15).astype(float),
                r5=(30 * F5[pos] - F5.sum()) / F5.sum(), r15=(30 * F15[pos] - F15.sum()) / F15.sum(),
                r15p=(30 * F15P[pos] - 15) / 15)

def boot_dif(v, dias, B=2000, semilla=7):
    """media e IC95 por bootstrap de jornadas."""
    u, g = np.unique(dias, return_inverse=True)
    s = np.bincount(g, v); c = np.bincount(g)
    rng = np.random.default_rng(semilla); idx = rng.integers(0, len(u), (B, len(u)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
