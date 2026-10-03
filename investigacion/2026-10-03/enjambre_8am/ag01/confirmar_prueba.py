# Confirmación en prueba (una sola vez) + reporte de vivo. Usa los multiplicadores fijados en dev.
import numpy as np, json
from scipy import stats
from candidatos import *
C = json.load(open(os.path.join(AQUI, "candidatos_dev.json")))
rng = np.random.default_rng(2026)
def top_hits(Q, y, n): return (np.argsort(-Q, 1)[:, :n] == y[:, None]).any(1)
for tramo in ("prueba", "vivo"):
    fl = [t for t in FIRST if TR[t] == tramo]; y = S[fl]
    print(f"\n===== {tramo} n={len(fl)} =====")
    for c in CANDS:
        lm, sg = C[c]["logm"], C[c]["signo"]
        O, E = stats_cand(fl, c); O = int(O)
        p1 = stats.poisson.sf(O - 1, E) if sg > 0 else stats.poisson.cdf(O, E)
        lo, hi = ic(O)
        Q = np.array([aplicar(t, lm, c) for t in fl]); B = PAJ[fl]
        g = 1000 * np.log2(Q[np.arange(len(y)), y] / B[np.arange(len(y)), y])
        bs = np.array([g[rng.integers(0, len(g), len(g))].mean() for _ in range(2000)])
        res = f"{c}: O={O} E={E:.1f} O/E={O/E:.2f} [{lo/E:.2f}; {hi/E:.2f}] p_unil={p1:.4f}  mbits {g.mean():+.1f} [{np.percentile(bs,2.5):+.1f}; {np.percentile(bs,97.5):+.1f}] P(<=0)={np.mean(bs<=0):.3f}"
        for n in (5, 15):
            hb, ha = top_hits(B, y, n), top_hits(Q, y, n)
            d = (ha.astype(float) - hb) * 30 / n          # cambio de retorno por ficha (pago 30)
            bsd = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)])
            res += f"\n    Top-{n}: {hb.sum()} -> {ha.sum()}  retorno/ficha base {hb.mean()*30/n-1:+.3f} ajustado {ha.mean()*30/n-1:+.3f}  Δ {d.mean():+.4f} [{np.percentile(bsd,2.5):+.4f}; {np.percentile(bsd,97.5):+.4f}]"
        print(res)
