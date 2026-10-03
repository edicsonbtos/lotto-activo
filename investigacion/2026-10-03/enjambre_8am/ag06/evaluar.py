# ag06 — evaluación única de los 3 candidatos pre-registrados (parámetros fijados en dev)
import os, numpy as np
from scipy import stats
AQUI = os.path.dirname(os.path.abspath(__file__))
R = np.load(os.path.join(AQUI, "rasgos.npz"))
TR, ERA, Y, PA, hd = R["TR"], R["ERA"], R["Y"], R["PA"], R["hdias"]
BIN = np.select([hd <= 1, hd <= 3, hd <= 6], [0, 1, 2], 3)
CAND = {
    "C1 hueco<=1 ×1,287": lambda: PA * np.where(BIN == 0, 1.287, 1.0),
    "C2 4 bins hueco": lambda: PA * np.array([1.170, 0.915, 0.967, 0.966])[BIN],
    "C3 temperatura β=0,967": lambda: PA ** 0.967,
}
rng = np.random.default_rng(6)

def ic_pois(o, e):
    lo = stats.chi2.ppf(0.025, 2 * o) / 2 if o > 0 else 0.0
    return lo / e, stats.chi2.ppf(0.975, 2 * o + 2) / 2 / e

def topk(Q, m, k):
    rk = np.argsort(np.argsort(-Q[m], axis=1), axis=1)
    return rk[np.arange(m.sum()), Y[m]] < k

TRAMOS = [("dev era 9:00", (TR == "dev") & (ERA == 9)), ("dev era 8:00", (TR == "dev") & (ERA == 8)),
          ("PRUEBA", TR == "prueba"), ("vivo", TR == "vivo")]
# O/E del bin hueco 0–1 contra P_aj
print("O/E hueco 0-1 día contra P_aj (descriptivo)")
for nom, m in TRAMOS:
    o = int((BIN[m][np.arange(m.sum()), Y[m]] == 0).sum()); e = float((PA[m] * (BIN[m] == 0)).sum())
    l, h = ic_pois(o, e); print(f"  {nom:13s} n={m.sum():3d} O={o} E={e:.1f} O/E={o/e:.2f} [{l:.2f},{h:.2f}]  "
                               f"P(≥O)={stats.poisson.sf(o-1, e):.3f}")
for cn, f in CAND.items():
    Q = f(); Q = Q / Q.sum(1, keepdims=True)
    print(f"\n== {cn}")
    for nom, m in TRAMOS:
        i = np.arange(m.sum())
        g = 1000 * np.log2(Q[m][i, Y[m]] / PA[m][i, Y[m]])
        B = rng.integers(0, len(g), (10000, len(g)))
        bm = g[B].mean(1)
        p = (bm <= 0).mean()
        t5b, t5c = topk(PA, m, 5).sum(), topk(Q, m, 5).sum()
        t15b, t15c = topk(PA, m, 15).sum(), topk(Q, m, 15).sum()
        # retorno por ficha (pago 30): Top-5 plano y Top-15 plano, diferencia candidato − actual con IC bootstrap
        d5 = (topk(Q, m, 5).astype(int) - topk(PA, m, 5)) * 30 / 5
        d15 = (topk(Q, m, 15).astype(int) - topk(PA, m, 15)) * 30 / 15
        r5 = d5[B].mean(1); r15 = d15[B].mean(1)
        print(f"  {nom:13s} n={len(g):3d} mbits {g.mean():+6.1f} [{np.percentile(bm,2.5):+.1f},{np.percentile(bm,97.5):+.1f}] "
              f"p(≤0)={p:.4f} | Top-5 {t5b}->{t5c}  Top-15 {t15b}->{t15c} | Δret/ficha T5 {d5.mean():+.3f} "
              f"[{np.percentile(r5,2.5):+.3f},{np.percentile(r5,97.5):+.3f}] T15 {d15.mean():+.3f} "
              f"[{np.percentile(r15,2.5):+.3f},{np.percentile(r15,97.5):+.3f}]")
