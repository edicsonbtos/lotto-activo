# ag05 — utilidades comunes: subserie de primeros sorteos y rasgos (solo pasado)
import os, numpy as np
from scipy import stats
AQUI = os.path.dirname(os.path.abspath(__file__))
d = np.load(os.path.join(AQUI, "..", "base8.npz"))
ip = np.where(d["es_primero"])[0]
Y = d["seq"][ip]; HR = d["hora"][ip]; TR = d["tramo"][ip]; FE = d["fecha"][ip]; DIA = d["dia"][ip]
PA = d["P_aj"][ip]
J = len(ip)
ERA = np.where(HR == 1, "9:00", "8:00")

# rasgos por fila j usando SOLO primeros sorteos anteriores (j' < j)
LAST = np.full((J, 38), 10**6)        # lag (en primeros sorteos) desde la última vez que el animal fue primer sorteo
C38 = np.zeros((J, 38), int); C76 = np.zeros((J, 38), int)
POS = np.zeros((J, 38, 16), bool)    # POS[j,a,k] = el primer sorteo de hace k (k=1..15) fue a
last = np.full(38, -10**6)
for j in range(J):
    LAST[j] = np.minimum(j - last, 10**6)
    for k in range(1, 16):
        if j - k >= 0: POS[j, Y[j - k], k] = True
    C38[j] = np.bincount(Y[max(0, j - 38):j], minlength=38)
    C76[j] = np.bincount(Y[max(0, j - 76):j], minlength=38)
    last[Y[j]] = j

def oe(mask_rows, G):
    """G: (J,38) bool grupo. O = nº filas con ganador en G; E = Σ P_aj[G]."""
    r = np.where(mask_rows)[0]
    O = int(G[r, Y[r]].sum()); E = float((PA[r] * G[r]).sum())
    return O, E

def ic_poisson(O, E):
    lo = stats.chi2.ppf(0.025, 2 * O) / 2 if O > 0 else 0.0
    hi = stats.chi2.ppf(0.975, 2 * O + 2) / 2
    return lo / E, hi / E

def p_dos(O, E):
    a = stats.poisson.cdf(O, E); b = stats.poisson.sf(O - 1, E)
    return min(1.0, 2 * min(a, b))

def mbits(q, rows):
    return 1000 * np.log2(q[rows, Y[rows]] / PA[rows, Y[rows]])

def boot(v, B=2000, seed=0):
    rng = np.random.default_rng(seed); n = len(v)
    bs = np.array([v[rng.integers(0, n, n)].mean() for _ in range(B)])
    return v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), (bs <= 0).mean()

def aplicar(mult):
    """mult: (J,38) multiplicadores; devuelve q renormalizada."""
    q = PA * mult
    return q / q.sum(1, keepdims=True)
