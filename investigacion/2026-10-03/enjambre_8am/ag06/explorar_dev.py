# ag06 — exploración SOLO en dev: O/E del motor P_aj en el primer sorteo por rasgo
import os, numpy as np
from scipy import stats, optimize
AQUI = os.path.dirname(os.path.abspath(__file__))
R = np.load(os.path.join(AQUI, "rasgos.npz"))
dev = R["TR"] == "dev"
ERA = R["ERA"]; Y = R["Y"]; PA = R["PA"]
NT = [0]

def ic(o, e):
    lo = stats.chi2.ppf(0.025, 2 * o) / 2 if o > 0 else 0.0
    hi = stats.chi2.ppf(0.975, 2 * o + 2) / 2
    return lo / e, hi / e

def pval(o, e):
    return min(1.0, 2 * min(stats.poisson.cdf(o, e), stats.poisson.sf(o - 1, e)))

def tabla(nombre, B):  # B: (filas, 38) entero de bin, -999 = ignorar
    bins = sorted(set(np.unique(B[dev])) - {-999})
    print(f"\n### {nombre}")
    print("bin | " + " | ".join(f"era{e}: O/E [IC] p" for e in (9, 8)) + " | dev: O E O/E p")
    for b in bins:
        out = []
        for e in (9, 8, None):
            m = dev & (ERA == e) if e else dev
            o = int((B[m, :][np.arange(m.sum()), Y[m]] == b).sum())
            ex = float((PA[m] * (B[m] == b)).sum())
            if e:
                l, h = ic(o, ex)
                out.append(f"{o}/{ex:.1f}={o/ex:.2f} [{l:.2f},{h:.2f}] p={pval(o,ex):.3f}")
            else:
                out.append(f"{o} {ex:.1f} {o/ex:.2f} p={pval(o,ex):.3f}")
                NT[0] += 1
        print(f"{b} | " + " | ".join(out))

# 1) puesto del ranking
RK = R["RANK"]
Bk = np.select([RK <= 5, RK <= 10, RK <= 15, RK <= 25], [1, 6, 11, 16], 26)
tabla("puesto en ranking P_aj (1=1-5, 6=6-10, 11=11-15, 16=16-25, 26=26-38)", Bk)

# 2) hueco en días (0 = salió ayer)
hd = R["hdias"]
Bh = np.minimum(hd, 7)
tabla("hueco en días desde la última aparición (0=ayer, 7=7+)", Bh)

# 3) horas exactas transcurridas (bins de 12 h)
hr = R["horas"]
edges = [0, 12, 18, 24, 30, 36, 48, 60, 72, 96, 144, 1e9]
Bhr = np.digitize(np.minimum(hr, 1e8), edges) - 1
print("\nbordes horas:", edges)
tabla("horas exactas desde la última aparición (bin = índice de borde)", Bhr)

# 4) apariciones en últimos 3 y 7 días
tabla("apariciones últimos 3 días (tope 3)", np.minimum(R["c3"], 3))
tabla("apariciones últimos 7 días (tope 5)", np.minimum(R["c7"], 5))

# 5) franja de ayer
tabla("franja de ayer (-1 no salió, 0 mañana 8-11, 1 tarde 12-15, 2 noche 16-19)", R["fr_ayer"])
print("\ncontrastes de bins mirados en dev (pooled):", NT[0])

# 6) temperatura: q ∝ PA^β
def nll(beta, m):
    L = beta * np.log(PA[m]); L -= L.max(1, keepdims=True)
    q = np.exp(L); q /= q.sum(1, keepdims=True)
    return -np.log2(q[np.arange(m.sum()), Y[m]]).mean()
print("\n### temperatura β (q ∝ P_aj^β)")
for nom, m in (("era9", dev & (ERA == 9)), ("era8", dev & (ERA == 8)), ("dev", dev)):
    r = optimize.minimize_scalar(lambda b: nll(b, m), bounds=(0.2, 3), method="bounded")
    g = 1000 * (nll(1.0, m) - r.fun)
    # error estándar aprox por curvatura
    h = 1e-3; c = (nll(r.x + h, m) - 2 * r.fun + nll(r.x - h, m)) / h**2 * m.sum() * np.log(2)
    print(f"{nom}: n={m.sum()} β*={r.x:.3f} ± {1/np.sqrt(c):.3f}  ganancia in-sample {g:+.1f} mbits")
# entropía media
for nom, m in (("era9", dev & (ERA == 9)), ("era8", dev & (ERA == 8))):
    Hm = -(PA[m] * np.log2(PA[m])).sum(1).mean()
    print(f"{nom}: entropía media P_aj {Hm:.3f} bits (uniforme {np.log2(38):.3f}); log-loss {nll(1.0,m):.3f}")
