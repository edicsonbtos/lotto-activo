# ag09 — utilidades comunes: primer sorteo por días ABIERTOS vs días de calendario
import os, numpy as np
from scipy import stats
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = np.load(os.path.join(BASE, "base8.npz"))
S, H, DI, F, DOW = Z["seq"], Z["hora"], Z["dia"], Z["fecha"], Z["dow"]
P, PAJ, E, T = Z["P"], Z["P_aj"], Z["es_primero"], Z["tramo"]
n = len(S)
first = {}                       # dia -> fila del primer sorteo
for t in range(n): first.setdefault(int(DI[t]), t)
dias = sorted(first)             # días abiertos
ordinal = {d: j for j, d in enumerate(dias)}
cuenta = {d: int((DI == d).sum()) for d in dias}
ERA8 = "2024-11-28"
MULT = {1: 0.272, 3: 1.736}

def previo(t, k, modo, misma_hora=True):
    """Fila del primer sorteo de hace k días (modo 'cal' o 'abierto'), o None."""
    d = int(DI[t])
    if modo == "cal":
        tp = first.get(d - k)
    else:
        j = ordinal[d] - k
        tp = first[dias[j]] if j >= 0 else None
    if tp is None: return None
    if misma_hora and H[tp] != H[t]: return None
    return tp

def filas_primero(tramo):
    return [first[d] for d in dias if T[first[d]] == tramo]

def ajustar(t, modo, mult=MULT, base=None, misma_hora=True):
    q = (P[t] if base is None else base).copy()
    for k, m in mult.items():
        tp = previo(t, k, modo, misma_hora)
        if tp is not None: q[S[tp]] *= m
    return q / q.sum()

def poisson_ic(o, e):
    lo = stats.chi2.ppf(0.025, 2 * o) / 2 if o > 0 else 0.0
    hi = stats.chi2.ppf(0.975, 2 * o + 2) / 2
    return o / e if e > 0 else np.nan, lo / e, hi / e

def oe(filas, target_fn, prob=None):
    """O/E del animal objetivo (target_fn(t) -> índice o None) contra el motor (prob, por defecto P)."""
    prob = P if prob is None else prob
    o = ex = 0.0; m = 0
    for t in filas:
        a = target_fn(t)
        if a is None: continue
        m += 1; o += S[t] == a; ex += prob[t, a]
    return m, int(o), ex

def mbits(filas, Q, base=None, B=2000, semilla=0):
    base = PAJ if base is None else base
    g = np.array([1000 * np.log2(Q[i][S[t]] / base[t, S[t]]) for i, t in enumerate(filas)])
    rng = np.random.default_rng(semilla)
    bs = [g[rng.integers(0, len(g), len(g))].mean() for _ in range(B)]  # 1 fila = 1 día
    return g.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), g
