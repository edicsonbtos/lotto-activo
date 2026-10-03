# -*- coding: utf-8 -*-
"""ag03 — evaluación ÚNICA de los 3 candidatos pre-registrados en prueba (y vivo, solo informativo)."""
import numpy as np, json
from scipy import stats
from comun import *
cfg = json.load(open("multiplicadores_dev.json")); M = cfg["M"]
M3 = {"dia": 0.584, "dia+1": 0.368}
dd = np.array([int(f[8:10]) for f in fecha]); h12 = ((8 + hora - 1) % 12) + 1
OBJ = {"dia": dd + 1, "dia+1": dd + 2, "hora12": h12 + 1}


def aplicar(rows, mult, base=None):
    q = (Paj[rows] if base is None else base).copy()
    for k, m in mult.items():
        idx = OBJ[k][rows]; ok = (idx >= 2) & (idx <= 37)
        q[np.where(ok)[0], idx[ok]] *= m
    return q / q.sum(1, keepdims=True)


def oe(rows, ref, objs):
    O = E = 0.0
    for k in objs:
        idx = OBJ[k][rows]; ok = (idx >= 2) & (idx <= 37)
        O += (seq[rows][ok] == idx[ok]).sum(); E += ref[np.where(ok)[0], idx[ok]].sum()
    return int(O), E


def topk_hits(q, rows, k):
    r = np.argsort(-q, 1)[:, :k]
    return (r == seq[rows][:, None]).any(1).astype(float)


rng = np.random.default_rng(1)
for tr in ("dev", "prueba", "vivo"):
    F = np.where(prim & (tramo == tr))[0]
    q1 = aplicar(F, {"dia": M["dia"], "dia+1": M["dia+1"]})
    q2 = aplicar(F, {"dia": M["dia"], "dia+1": M["dia+1"], "hora12": M["hora12"]})
    q3 = aplicar(F, M3)
    print(f"\n=== {tr} (n={len(F)}) ===")
    for nom, q, ref, objs in (("C1_fecha", q1, Paj[F], ["dia", "dia+1"]),
                              ("C2_fecha_hora", q2, Paj[F], ["dia", "dia+1", "hora12"]),
                              ("C3_primer_esquiva_mas", q3, q1, ["dia", "dia+1"])):
        O, E = oe(F, ref, objs); lo, hi = poisson_ic(O)
        p = stats.poisson.cdf(O, E)
        m, mlo, mhi = mbits_boot(q, F, rng=rng)
        g = 1000 * np.log2(q[np.arange(len(F)), seq[F]] / Paj[F, seq[F]])
        pb = np.mean([g[rng.integers(0, len(g), len(g))].mean() <= 0 for _ in range(4000)])
        s = f"{nom:22s} O={O} E={E:.1f} O/E={O/E:.2f} [{lo/E:.2f};{hi/E:.2f}] p_unil={p:.4f} | mbits/primer {m:+.1f} [{mlo:+.1f};{mhi:+.1f}] P(<=0)={pb:.3f}"
        for k in (5, 15):
            a = topk_hits(Paj[F], F, k); b = topk_hits(q, F, k)
            d = (30 * b / k) - (30 * a / k)          # cambio de retorno por ficha (Top-k plano)
            bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
            s += f" | Top-{k} {int(a.sum())}->{int(b.sum())} Δret/ficha {100*d.mean():+.1f}% [{100*np.percentile(bs,2.5):+.1f};{100*np.percentile(bs,97.5):+.1f}]"
        print(s)
