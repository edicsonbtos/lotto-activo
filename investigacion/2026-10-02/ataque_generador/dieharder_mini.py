"""Versión mínima de pruebas estilo Diehard/Dieharder que caben en ~7.000 símbolos (el Dieharder real pide millones)."""
import sys, json
from pathlib import Path
import numpy as np
from scipy import stats
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "herramientas"))
import lotto_eval as LE
D = LE.cargar(); s = D.seq[2000:9357]; K = 38; n = len(s); out = {}
rng = np.random.default_rng(20261002)

# 1) Gap test: huecos entre apariciones de cada símbolo ~ geométrica(1/38)
gaps = []
for k in range(K):
    p = np.flatnonzero(s == k); gaps.extend(np.diff(p) - 1)
gaps = np.array(gaps); q = 1 / K; edges = [0, 10, 20, 40, 60, 90, 130, 10 ** 6]
cnt = np.histogram(gaps, edges)[0]
pr = np.array([(1 - q) ** a - (1 - q) ** b for a, b in zip(edges[:-1], edges[1:])])
chi = ((cnt - len(gaps) * pr) ** 2 / (len(gaps) * pr)).sum(); out["gap"] = float(stats.chi2.sf(chi, len(pr) - 1))

# 2) Poker: grupos de 5 sorteos, nº de símbolos distintos (distribución exacta por Stirling)
from math import comb
def stirling2(n_, k_):
    S = [[0] * (k_ + 1) for _ in range(n_ + 1)]; S[0][0] = 1
    for i in range(1, n_ + 1):
        for j in range(1, k_ + 1): S[i][j] = j * S[i - 1][j] + S[i - 1][j - 1]
    return S[n_][k_]
pd = {d: stirling2(5, d) * np.prod([K - i for i in range(d)]) / K ** 5 for d in range(1, 6)}
g = s[: n // 5 * 5].reshape(-1, 5); dist = np.array([len(set(r)) for r in g])
c = np.array([(dist <= 3).sum()] + [(dist == d).sum() for d in (4, 5)]); e = len(g) * np.array([sum(pd[d] for d in (1, 2, 3)), pd[4], pd[5]])
out["poker"] = float(stats.chi2.sf(((c - e) ** 2 / e).sum(), 2))

# 3) Runs-up (Knuth) sobre los índices: longitud de tramos crecientes
x = s.astype(float) + rng.random(n) * 1e-6 * 0  # empates: se parte el tramo (>=)
runs = []; L = 1
for i in range(1, n):
    if s[i] > s[i - 1]: L += 1
    else: runs.append(L); L = 1
runs = np.array(runs); m = len(runs)
# con empates posibles (P(igual)=1/38) se compara contra simulación
def runs_sim(sq):
    r = []; L = 1
    for i in range(1, len(sq)):
        if sq[i] > sq[i - 1]: L += 1
        else: r.append(L); L = 1
    return np.bincount(np.minimum(r, 5), minlength=6)[1:]
obs = runs_sim(s); sims = np.array([runs_sim(rng.permutation(s)) for _ in range(2000)])
mu, sd = sims.mean(0), sims.std(0)
stat = (((obs - mu) / sd) ** 2).sum(); ss = (((sims - mu) / sd) ** 2).sum(1)
out["runs_up"] = float(((ss >= stat).sum() + 1) / 2001)

# 4) Birthday spacings (pares de sorteos consecutivos de 3: tupla de 3 símbolos -> id, colisiones en bloques de 40)
def birthday(sq):
    t = sq[: len(sq) // 3 * 3].reshape(-1, 3); ids = t[:, 0] * K * K + t[:, 1] * K + t[:, 2]
    tot = 0
    for i in range(0, len(ids) - 39, 40):
        b = np.sort(ids[i:i + 40]); sp = np.sort(np.diff(b)); tot += (np.diff(sp) == 0).sum()
    return tot
o = birthday(s); sm = np.array([birthday(rng.permutation(s)) for _ in range(2000)])
out["birthday"] = {"obs": int(o), "media_perm": float(sm.mean()), "p": float(((sm >= o).sum() + 1) / 2001)}
Path(__file__).with_name("SALIDA_dieharder_mini.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
