# -*- coding: utf-8 -*-
"""Verifica el texto 'Motor Contrarian' (PREREGISTRO_contrarian.md). Solo desarrollo."""
import json, os, sys
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K, B = 38, 5000
F5 = np.array([2, 2, 2, 1, 1] + [0] * (K - 5))
z = np.load(os.path.join(RAIZ, "herramientas", "exploracion", "calor_cache.npz"))
P, y = z["P"], z["y"]
la = LE.cargar(); a, b = LE.W, LE.CORTE_FIJO
seq = la.seq; hora = la.hora[a:b]; fecha = np.array(la.fecha)[a:b]
n = len(y); rng = np.random.default_rng(20261002)
LO, HI = 100 * 0.0083 / 2, 100 - 100 * 0.0083 / 2   # IC 99,17 %
u = np.unique(fecha); mit = np.isin(fecha, u[: len(u) // 2])

# hueco en sorteos antes de cada sorteo t (1 = salió en el sorteo anterior)
ult = np.full(K, -10**6); gap = np.zeros((len(seq), K), int)
for t, s in enumerate(seq):
    gap[t] = t - ult; ult[s] = t
G = gap[a:b]
C1 = G > 12; C2 = G <= 2; C3 = (G >= 5) & (G <= 8)
ar = np.arange(n)


def boot(num, den, g):
    uu, gi = np.unique(g, return_inverse=True)
    N = np.bincount(gi, num, len(uu)); D = np.bincount(gi, den, len(uu))
    k = rng.integers(0, len(uu), (B, len(uu)))
    bs = N[k].sum(1) / D[k].sum(1)
    return N.sum() / D.sum(), np.percentile(bs, [LO, HI])


def oe(M, mask=None):
    m = np.ones(n, bool) if mask is None else mask
    return boot(M[ar, y][m].astype(float), (P * M).sum(1)[m], fecha[m])


def halves(M):
    return [(M[ar, y][mm].sum() / (P * M).sum(1)[mm].sum()) for mm in (mit, ~mit)]


res = {}
print(f"n={n}; animales por sorteo: C1 {C1.sum(1).mean():.1f}, C2 {C2.sum(1).mean():.1f}, C3 {C3.sum(1).mean():.1f} de 38")
for nom, M, sentido in [("C1 atrasados >12 sorteos", C1, -1), ("C2 salió en últimos 2", C2, -1), ("C3 zona muerta 5-8", C3, +1)]:
    v, ic = oe(M); h = halves(M)
    azar = M.sum() / K
    pasa = (ic[1] < 1 and max(h) < 1) if sentido < 0 else (ic[0] > 1 and min(h) > 1)
    print(f"{nom}: salieron {M[ar, y].sum()} (azar {azar:.0f}, ensamble {(P*M).sum():.0f}); O/E ensamble {v:.3f} IC[{ic[0]:.3f};{ic[1]:.3f}] mitades {h[0]:.3f}/{h[1]:.3f} -> {'PASA' if pasa else 'NO PASA'}")
    res[nom] = dict(oe=v, ic=ic.tolist(), mitades=h, pasa=bool(pasa))

# C4: hora 0 vs resto
m0 = hora == 0
v0, ic0 = oe(C1, m0); v1, ic1 = oe(C1, ~m0)
pasa4 = ic0[0] <= 1 <= ic0[1] and ic1[1] < 1
print(f"C4 C1 en 8:00: O/E {v0:.3f} IC[{ic0[0]:.3f};{ic0[1]:.3f}] (n={m0.sum()}) | resto {v1:.3f} IC[{ic1[0]:.3f};{ic1[1]:.3f}] -> {'PASA' if pasa4 else 'NO PASA'}")
for nom, M in [("C2", C2), ("C3", C3)]:
    print(f"   descriptivo {nom}: 8:00 {oe(M, m0)[0]:.3f} | resto {oe(M, ~m0)[0]:.3f}")
res["C4"] = dict(h0=v0, ic0=ic0.tolist(), resto=v1, ic1=ic1.tolist(), pasa=bool(pasa4))

# C5: terminación walk-forward (label numérico, "00" = 0)
num_lab = np.array([0 if l == "00" else int(l) for l in LE.POS]); term = num_lab % 10
T = np.ones((10, 10)); mejora = np.zeros(n)
tm = np.zeros(K, int)
for k in range(K): tm[k] = term[k]
# pasado: contar transiciones con todo lo anterior a t (desde 0), actualizar secuencialmente
for t in range(1, a):
    T[term[seq[t - 1]], term[seq[t]]] += 1
for i, t in enumerate(range(a, b)):
    prev = term[seq[t - 1]]
    pi = T[prev] / T[prev].sum()                    # P(term siguiente | term previa)
    marg = T.sum(0) / T.sum()
    f = (pi / marg)[term]                            # factor por animal
    Q = P[i] * f; Q /= Q.sum()
    mejora[i] = np.log(Q[y[i]]) - np.log(P[i, y[i]])
    T[term[seq[t - 1]], term[seq[t]]] += 1
mu, ic5 = boot(mejora, np.ones(n), fecha)
mh = [mejora[mm].mean() for mm in (mit, ~mit)]
pasa5 = ic5[0] > 0 and min(mh) > 0
print(f"C5 terminación: mejora log-verosimilitud {mu*1000:+.2f} mnats/sorteo IC[{ic5[0]*1000:+.2f};{ic5[1]*1000:+.2f}] mitades {mh[0]*1000:+.2f}/{mh[1]*1000:+.2f} -> {'PASA' if pasa5 else 'NO PASA'}")
res["C5"] = dict(mejora=mu, ic=ic5.tolist(), mitades=mh, pasa=bool(pasa5))

# C6: estrategia completa
mult = np.ones((n, K)); mult[C1] = 0.5; mult[C2 & ~C1] = 0.7; mult[C3] = 1.3
mult[hora == 0] = 1.0
Q = P * mult; Q /= Q.sum(1, keepdims=True)


def retorno(PP):
    o = np.argsort(-PP, 1, kind="stable")
    pu = (o == y[:, None]).argmax(1)
    return 30 * F5[pu] - F5.sum()


r0, r1 = retorno(P), retorno(Q)
d, ic6 = boot(r1 - r0, np.full(n, 8.0), fecha)
mm6 = [(r1 - r0)[mm].mean() / 8 for mm in (mit, ~mit)]
pasa6 = ic6[0] > 0 and min(mm6) > 0
a0 = r0.sum() / (8 * n); a1 = r1.sum() / (8 * n)
print(f"C6 estrategia: normal {a0*100:+.1f} %, contrarian {a1*100:+.1f} %, dif {d*100:+.1f} pp IC[{ic6[0]*100:+.1f};{ic6[1]*100:+.1f}] mitades {mm6[0]*100:+.1f}/{mm6[1]*100:+.1f} -> {'PASA' if pasa6 else 'NO PASA'}")
print(f"   Top-5 cambia en {(np.argsort(-P,1)[:, :5] != np.argsort(-Q,1)[:, :5]).any(1).mean()*100:.0f} % de los sorteos")
res["C6"] = dict(normal=a0, contrarian=a1, dif=d, ic=ic6.tolist(), mitades=mm6, pasa=bool(pasa6))
json.dump(res, open(os.path.join(os.path.dirname(__file__), "contrarian_dev.json"), "w"), indent=1, default=float)
