# Utilidades comunes ag01: construye el mapa de rasgos (k, j) del primer sorteo
import os, numpy as np
from scipy import stats
AQUI = os.path.dirname(os.path.abspath(__file__))
d = np.load(os.path.join(AQUI, "..", "base8.npz"), allow_pickle=True)
S, H, DI, F, P, PAJ, EP, TR = (d[k] for k in ("seq", "hora", "dia", "fecha", "P", "P_aj", "es_primero", "tramo"))
# sorteos de cada día, en orden
DIAS = {}
for t in range(len(S)):
    DIAS.setdefault(int(DI[t]), []).append(t)
FIRST = np.where(EP)[0]

def ganador(dia, j):
    """ganador de la posición j del día; j='ult' -> último. None si no existe."""
    L = DIAS.get(dia)
    if L is None: return None
    if j == "ult": return int(S[L[-1]])
    if j >= len(L): return None
    return int(S[L[j]])

def rasgos():
    R = [("A", k, j) for k in range(1, 15) for j in range(12)]
    R += [("A", k, 0) for k in range(15, 31)]          # B: primero de hace k
    R += [("U", k, "ult") for k in range(15, 31)]      # C: último de hace k (k<=14 ya en A)
    return R

def objetivo(t, k, j):
    return ganador(int(DI[t]) - k, j)

def poisson_p2(O, E):
    lo = stats.poisson.cdf(O, E); hi = stats.poisson.sf(O - 1, E)
    return min(1.0, 2 * min(lo, hi))

def ic(O, a=0.05):
    lo = 0 if O == 0 else stats.chi2.ppf(a/2, 2*O)/2
    hi = stats.chi2.ppf(1-a/2, 2*O+2)/2
    return lo, hi

def oe(filas, k, j, Pm=PAJ):
    O = 0; E = 0.0; n = 0
    for t in filas:
        a = objetivo(t, k, j)
        if a is None: continue
        n += 1; O += int(S[t] == a); E += Pm[t, a]
    return O, E, n

def bh(p):
    p = np.asarray(p); m = len(p); o = np.argsort(p)
    q = p[o] * m / np.arange(1, m+1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(m); out[o] = np.minimum(q, 1); return out
