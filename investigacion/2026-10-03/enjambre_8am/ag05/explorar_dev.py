# ag05 — exploración SOLO en dev (y 'cal' para conteos crudos). No toca prueba ni vivo.
import numpy as np
from scipy import stats
from comun import *

DEV = TR == "dev"; CAL = TR == "cal"
E9 = DEV & (ERA == "9:00"); E8 = DEV & (ERA == "8:00")
CRU = CAL | DEV            # conteos crudos contra 1/38
nmir = 0

def fila(nombre, G):
    global nmir; nmir += 1
    out = [nombre]
    for m in (E9, E8, DEV):
        O, E = oe(m, G); lo, hi = ic_poisson(O, E)
        out.append(f"{O:4d}/{E:6.1f}={O/E:4.2f}[{lo:.2f};{hi:.2f}]")
    O, E = oe(DEV, G); out.append(f"p={p_dos(O, E):.3f}")
    r = np.where(CRU)[0]; Oc = int(G[r, Y[r]].sum()); Ec = G[r].sum() / 38
    out.append(f"crudo cal+dev {Oc}/{Ec:.1f}={Oc/Ec:.2f}")
    print(" | ".join(out))

print("=== (1a) Evitación acumulada C_k: salió como primer sorteo en los últimos k  [9:00 dev | 8:00 dev | dev]")
for k in range(1, 16):
    fila(f"C_{k:2d}", POS[:, :, 1:k + 1].any(2))
print("\n=== (1b) Por posición exacta: el primer sorteo de hace k")
for k in range(1, 16):
    fila(f"pos{k:2d}", POS[:, :, k])
print("\n=== (1c) C_k sin las posiciones 1 y 3 (ya en P_aj)")
for k in (5, 8, 10, 15):
    G = POS[:, :, [i for i in range(2, k + 1) if i != 3]].any(2)
    fila(f"C_{k:2d}\\{{1,3}}", G)

print("\n=== (4) Hueco: última aparición como primer sorteo hace L (hazard contra P_aj)")
bins = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 10), (11, 20), (21, 38), (39, 76), (77, 152), (153, 10**7)]
for a, b in bins:
    fila(f"L {a}-{b if b < 10**6 else 'inf'}", (LAST >= a) & (LAST <= b))

print("\n=== (3) Balanceo: nº de apariciones como primer sorteo en los últimos 38 / 76")
for c in (0, 1, 2):
    fila(f"c38={c}", C38 == c)
fila("c38>=3", C38 >= 3)
for c in (0, 1, 2, 3):
    fila(f"c76={c}", C76 == c)
fila("c76>=4", C76 >= 4)
# tendencia (regresión log-lineal) en dev: log q = log P_aj + b*(c - media)
def ajuste_b(C, rows):
    r = np.where(rows)[0]
    x = C[r] - C[r].mean(1, keepdims=True)
    def nll(b):
        q = PA[r] * np.exp(b * x); q /= q.sum(1, keepdims=True)
        return -np.log(q[np.arange(len(r)), Y[r]]).sum()
    from scipy.optimize import minimize_scalar
    res = minimize_scalar(nll, bounds=(-2, 2), method="bounded")
    lr = 2 * (nll(0) - res.fun)
    return res.x, lr, stats.chi2.sf(lr, 1)
for nm, C in (("c38", C38), ("c76", C76)):
    nmir += 1
    for lab, m in (("9:00", E9), ("8:00", E8), ("dev", DEV)):
        b, lr, p = ajuste_b(C, m)
        print(f"tendencia {nm} {lab}: b={b:+.3f} LR={lr:.2f} p={p:.3f}")

print("\n=== (2) Coleccionista y distintos en ventanas")
def T_coleccion(y):
    n = len(y); T = []
    for s in range(n):
        seen = set(); 
        for t in range(s, n):
            seen.add(y[t])
            if len(seen) == 38: T.append(t - s + 1); break
    return np.array(T)
def distintos(y, w):
    return np.array([len(set(y[s:s + w])) for s in range(len(y) - w + 1)])
rng = np.random.default_rng(1)
idx = {"cal+dev": np.where(CRU)[0], "dev": np.where(DEV)[0]}
for nm, r in idx.items():
    y = Y[r]
    Tobs = T_coleccion(y).mean(); D38 = distintos(y, 38).mean(); D19 = distintos(y, 19).mean()
    sims = []
    for _ in range(300):
        ys = rng.integers(0, 38, len(y))
        sims.append((T_coleccion(ys).mean(), distintos(ys, 38).mean(), distintos(ys, 19).mean()))
    sims = np.array(sims)
    print(f"{nm} n={len(y)} azar: T={Tobs:.1f} (sim {sims[:,0].mean():.1f}, P(sim<=obs)={(sims[:,0]<=Tobs).mean():.3f}) "
          f"D38={D38:.2f} (sim {sims[:,1].mean():.2f}, P(sim>=obs)={(sims[:,1]>=D38).mean():.3f}) "
          f"D19={D19:.2f} (sim {sims[:,2].mean():.2f}, P(sim>=obs)={(sims[:,2]>=D19).mean():.3f})")
    if nm == "dev":
        sims = []
        cum = PA[r].cumsum(1)
        for _ in range(300):
            u = rng.random(len(r)); ys = (u[:, None] > cum).sum(1).clip(0, 37)
            sims.append((T_coleccion(ys).mean(), distintos(ys, 38).mean(), distintos(ys, 19).mean()))
        sims = np.array(sims)
        print(f"{nm} bajo P_aj: T sim {sims[:,0].mean():.1f} P(sim<=obs)={(sims[:,0]<=Tobs).mean():.3f}; "
              f"D38 sim {sims[:,1].mean():.2f} P(sim>=obs)={(sims[:,1]>=D38).mean():.3f}; "
              f"D19 sim {sims[:,2].mean():.2f} P(sim>=obs)={(sims[:,2]>=D19).mean():.3f}")
nmir += 6
# gaps crudos vs geométrica (cal+dev)
r = np.where(CRU)[0]; y = Y[r]; gaps = []
lastp = {}
for t, a in enumerate(y):
    if a in lastp: gaps.append(t - lastp[a])
    lastp[a] = t
gaps = np.array(gaps)
edges = [1, 2, 3, 4, 6, 11, 21, 39, 77, 10**6]
obs = np.histogram(gaps, edges)[0]
p = 1 / 38; cdf = lambda g: 1 - (1 - p) ** (g - 1)    # P(gap < g)
pr = np.array([cdf(edges[i + 1]) - cdf(edges[i]) for i in range(len(edges) - 1)]); pr /= pr.sum()
ex = pr * len(gaps)
print("\n(4 crudo) huecos cal+dev:", [f"{edges[i]}-{edges[i+1]-1}: {obs[i]}/{ex[i]:.1f}" for i in range(len(obs))])
chi = ((obs - ex) ** 2 / ex).sum(); print(f"chi2={chi:.1f} gl={len(obs)-1} p={stats.chi2.sf(chi, len(obs)-1):.4f}; media hueco={gaps.mean():.1f} (geom 38)")
nmir += 1
print("\nCosas miradas en dev (contrastes):", nmir)
